"""
ReflectoApp — main application window (PySide6 + pyqtgraph rewrite).

Replaces the tkinter ReflectoApp.  Physics code is unchanged.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from PySide6.QtCore import (
    QThread,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
)

from ..materials import MaterialLibrary
from ..stack import StackConfig
from ..tmm import r_to_observables, t_to_observables
from .compute_worker import ComputeWorker
from .palette import (
    AX_BG, BG_DARK, LABEL_COL, PALETTE, SPINE_COL, TICK_COL,
)
from .plot_panel import PlotPanel
from .stack_editor import StackEditor
from .ui_compiled.ui_main_window import Ui_MainWindow

_DEBOUNCE_MS = 250


class ReflectoApp(QMainWindow):
    """Top-level application window."""

    # Signal to invoke worker.run() across thread boundary
    _run_requested = Signal(object)
    _warmup_requested = Signal()

    def __init__(self, lib: MaterialLibrary) -> None:
        super().__init__()
        self.lib = lib

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setMinimumSize(1200, 640)

        # State
        self._computing   = False
        self._last_r:     np.ndarray | None = None
        self._last_t:     np.ndarray | None = None
        self._last_lam:   np.ndarray | None = None
        self._last_N0_arr: np.ndarray | None = None
        self._last_Ns_arr: np.ndarray | None = None
        self._last_R_eff: np.ndarray | None = None
        self._last_T_eff: np.ndarray | None = None
        self._last_mode:  str = "spectrum"

        # Inject custom widgets into .ui containers
        self._build_custom_widgets(list(lib.available()))

        # Debounce timer
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._compute)

        # Background worker
        self._thread = QThread(self)
        self._worker = ComputeWorker(lib)
        self._worker.moveToThread(self._thread)
        self._worker.result_ready.connect(self._on_result, Qt.QueuedConnection)
        self._worker.error_occurred.connect(self._on_error, Qt.QueuedConnection)
        self._worker.progress_changed.connect(self._set_status, Qt.QueuedConnection)
        # Route compute/warmup to worker across thread boundary via signals
        self._run_requested.connect(self._worker.run)
        self._warmup_requested.connect(self._worker.warmup)
        self._thread.start()

        # Wire UI signals
        self._connect_signals()

        # JIT warmup
        self._warmup_requested.emit()

    # ------------------------------------------------------------------
    # Custom widget injection (PlotPanel + StackEditor into .ui containers)
    # ------------------------------------------------------------------

    def _build_custom_widgets(self, mat_keys: list[str]) -> None:
        # PlotPanel → centre_container
        self.plot_panel = PlotPanel()
        vl_c = QVBoxLayout(self.ui.centre_container)
        vl_c.setContentsMargins(0, 0, 0, 0)
        vl_c.addWidget(self.plot_panel)

        # StackEditor → left_container (below the title label)
        self.stack_editor = StackEditor()
        self.stack_editor.update_materials(mat_keys)
        self.ui.left_container.layout().addWidget(self.stack_editor)
        self.stack_editor.changed.connect(self._schedule_recompute)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        ui = self.ui

        # Wavelength entries
        for edit in (ui.edit_lam_min, ui.edit_lam_max, ui.edit_lam_step):
            edit.textChanged.connect(self._schedule_recompute)

        # Angle
        ui.edit_angle.textChanged.connect(self._schedule_recompute)

        # Polarisation
        for rb in (ui.radio_pol_s, ui.radio_pol_p, ui.radio_pol_both):
            rb.toggled.connect(
                lambda checked: checked and self._schedule_recompute()
            )

        # Display options
        ui.chk_unwrap.toggled.connect(self._on_unwrap_toggle)
        ui.chk_autofit.toggled.connect(self._on_autofit_toggle)
        ui.chk_log_y.toggled.connect(self._on_log_y_toggle)

        # NA
        ui.edit_na.textChanged.connect(self._schedule_recompute)
        ui.chk_use_na.toggled.connect(self._on_na_toggle)

        # Buttons
        ui.btn_compute.clicked.connect(self._compute)
        ui.btn_clear_plot.clicked.connect(self.plot_panel.clear)
        ui.btn_save_csv.clicked.connect(self._export_csv)
        ui.btn_save_png.clicked.connect(self._export_png)

        # Menu
        ui.action_open.triggered.connect(self._open_stack)
        ui.action_save.triggered.connect(self._save_stack)
        ui.action_exit.triggered.connect(self.close)

    # ------------------------------------------------------------------
    # Compute scheduling
    # ------------------------------------------------------------------

    @Slot()
    def _schedule_recompute(self) -> None:
        self._debounce.start()

    def _gather_params(self) -> dict | None:
        """Validate UI fields and return a params dict, or None on error."""
        ui = self.ui
        try:
            lam_min  = float(ui.edit_lam_min.text())
            lam_max  = float(ui.edit_lam_max.text())
            lam_step = float(ui.edit_lam_step.text())
            theta    = float(ui.edit_angle.text())
        except ValueError:
            self._set_status("Invalid parameter values.")
            return None

        if lam_min >= lam_max or lam_step <= 0:
            self._set_status("Invalid wavelength range.")
            return None

        use_na = ui.chk_use_na.isChecked()
        na_val = 0.0
        if use_na:
            try:
                na_val = float(ui.edit_na.text())
            except ValueError:
                self._set_status("Invalid NA value.")
                return None
            if na_val <= 0.0:
                use_na = False

        lam_array = np.arange(lam_min, lam_max + lam_step * 0.5, lam_step)
        config    = self.stack_editor.get_config()

        if not config.layers:
            self._set_status("Add at least one layer.")
            return None

        pol = "s"
        if ui.radio_pol_p.isChecked():
            pol = "p"
        elif ui.radio_pol_both.isChecked():
            pol = "both"

        # Check sweep modes
        for i, layer in enumerate(config.layers):
            if layer.sweep_mode == "material" and len(layer.sweep_materials) >= 2:
                import numpy as _np
                return {
                    "mode":         "sweep",
                    "lam_array":    lam_array,
                    "config":       config,
                    "layer_index":  i,
                    "materials":    layer.sweep_materials,
                    "theta":        theta,
                    "pol":          pol,
                    "use_na":       use_na,
                    "na_val":       na_val,
                }
            if layer.sweep_mode == "mix" and layer.sweep_mat_b:
                return {
                    "mode":         "mix_sweep",
                    "lam_array":    lam_array,
                    "config":       config,
                    "layer_index":  i,
                    "mat_a":        layer.material,
                    "mat_b":        layer.sweep_mat_b,
                    "model":        layer.sweep_mix_model,
                    "f_values":     np.linspace(0.0, 1.0, layer.sweep_n_pts).tolist(),
                    "theta":        theta,
                    "pol":          pol,
                    "use_na":       use_na,
                    "na_val":       na_val,
                }

        if use_na:
            return {
                "mode":      "na",
                "lam_array": lam_array,
                "config":    config,
                "na_val":    na_val,
                "pol":       pol,
            }

        return {
            "mode":      "spectrum",
            "lam_array": lam_array,
            "config":    config,
            "theta":     theta,
            "pol":       pol,
        }

    @Slot()
    def _compute(self) -> None:
        if self._computing:
            return
        params = self._gather_params()
        if params is None:
            return
        self._computing = True
        self._set_status("Computing\u2026")
        self._run_requested.emit(params)

    # ------------------------------------------------------------------
    # Result dispatch
    # ------------------------------------------------------------------

    @Slot(object)
    def _on_result(self, payload: dict) -> None:
        self._computing = False
        mode = payload["mode"]
        if mode == "spectrum":
            self._handle_spectrum(payload)
        elif mode == "na":
            self._handle_na(payload)
        elif mode == "sweep":
            self._handle_sweep(payload)
        elif mode == "mix_sweep":
            self._handle_mix_sweep(payload)

    @Slot(str)
    def _on_error(self, msg: str) -> None:
        self._computing = False
        self._set_status(msg)

    def _handle_spectrum(self, p: dict) -> None:
        lam   = p["lam"]
        amp   = p["amp"]
        R     = p["R"]
        phi   = p["phi"]
        amp_t = p["amp_t"]
        T_t   = p["T_t"]
        phi_t = p["phi_t"]

        self._last_r     = p["r"]
        self._last_t     = p["t"]
        self._last_lam   = lam
        self._last_N0_arr = p["N0_arr"]
        self._last_Ns_arr = p["Ns_arr"]
        self._last_R_eff = None
        self._last_T_eff = None
        self._last_mode  = "spectrum"

        config = self.stack_editor.get_config()
        label  = " / ".join(lay.name for lay in config.layers)
        self.plot_panel.set_unwrap(self.ui.chk_unwrap.isChecked())
        self.plot_panel.plot(lam, amp, R, phi, amp_t, T_t, phi_t, label=label, clear=True)

        mid = len(lam) // 2
        status = f"Done \u2014 {len(lam)} pts\n@{lam[mid]:.0f}nm: |r|={amp[mid]:.3f} R={R[mid]:.3f}"
        if T_t is not None:
            status += f" T={T_t[mid]:.3f}"
        self._set_status(status)

    def _handle_na(self, p: dict) -> None:
        lam           = p["lam"]
        R_eff         = p["R_eff"]
        T_eff         = p["T_eff"]
        na_val        = p["na_val"]
        theta_max_deg = p["theta_max_deg"]

        self._last_R_eff = R_eff
        self._last_T_eff = T_eff
        self._last_lam   = lam
        self._last_mode  = "na"
        self._last_r     = None
        self._last_t     = None

        self.plot_panel.plot_na_result(lam, R_eff, T_eff, label=f"NA={na_val:.2f}")
        self._set_status(
            f"Done \u2014 NA={na_val:.2f}  \u03b8max={theta_max_deg:.1f}\u00b0\n{len(lam)} pts"
        )

    def _handle_sweep(self, p: dict) -> None:
        results = p["results"]
        errors  = p["errors"]
        if not results:
            self._set_status("Sweep: no valid materials.")
            return
        self.plot_panel.clear()
        for i, entry in enumerate(results):
            if entry["is_na"]:
                self.plot_panel.plot_na_result(
                    entry["lam"], entry["R"], entry["T_t"],
                    label=entry["label"], color_idx=i, clear=False,
                )
            else:
                self.plot_panel.plot(
                    entry["lam"], entry["amp"], entry["R"], entry["phi"],
                    entry["amp_t"], entry["T_t"], entry["phi_t"],
                    label=entry["label"], color_idx=i, clear=False,
                )
        self._last_r    = None
        self._last_lam  = results[0]["lam"]
        self._last_mode = "sweep"
        msg = f"Sweep: {len(results)} materials"
        if errors:
            msg += f" ({len(errors)} range errors)"
        self._set_status(msg)

    def _handle_mix_sweep(self, p: dict) -> None:
        results = p["results"]
        errors  = p["errors"]
        mat_a   = p["mat_a"]
        mat_b   = p["mat_b"]
        if not results:
            self._set_status("Mix sweep: no valid points.")
            return

        import colorsys
        try:
            import matplotlib.cm as _cm
            cmap = _cm.get_cmap("plasma")
            def _col(f: float) -> str:
                r, g, b, _ = cmap(float(f))
                return "#{:02x}{:02x}{:02x}".format(
                    int(r * 255), int(g * 255), int(b * 255)
                )
        except Exception:
            def _col(f: float) -> str:
                h = f * 0.8
                r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
                return "#{:02x}{:02x}{:02x}".format(
                    int(r * 255), int(g * 255), int(b * 255)
                )

        self.plot_panel.clear()
        for entry in results:
            col = _col(entry["f"])
            if entry["is_na"]:
                self.plot_panel.plot_na_result(
                    entry["lam"], entry["R"], entry["T_t"],
                    color_idx=0, clear=False,
                )
            else:
                self.plot_panel.plot(
                    entry["lam"], entry["amp"], entry["R"], entry["phi"],
                    entry["amp_t"], entry["T_t"], entry["phi_t"],
                    color=col, clear=False,
                )
        self.plot_panel.add_colorbar("plasma", 0.0, 1.0, f"f  ({mat_a} \u2192 {mat_b})")

        self._last_r    = None
        self._last_lam  = results[0]["lam"]
        self._last_mode = "sweep"
        msg = f"Mix sweep: {len(results)} pts  {mat_a} -> {mat_b}"
        if errors:
            msg += f"  ({len(errors)} errors)"
        self._set_status(msg)

    # ------------------------------------------------------------------
    # Display option toggles
    # ------------------------------------------------------------------

    @Slot(bool)
    def _on_unwrap_toggle(self, checked: bool) -> None:
        self.plot_panel.set_unwrap(checked)
        self._replot_last()

    @Slot(bool)
    def _on_autofit_toggle(self, checked: bool) -> None:
        self.plot_panel.set_autofit(checked)
        self._replot_last()

    @Slot(bool)
    def _on_log_y_toggle(self, checked: bool) -> None:
        self.plot_panel.set_log_y(checked)
        self._replot_last()

    def _replot_last(self) -> None:
        if self._last_r is None:
            return
        pol   = self._current_pol()
        angle = self._current_angle()
        amp, R, phi = r_to_observables(self._last_r)
        amp_t, T_t, phi_t = (None, None, None)
        if self._last_t is not None:
            amp_t, T_t, phi_t = t_to_observables(
                self._last_t, self._last_N0_arr, self._last_Ns_arr, angle, pol
            )
        config = self.stack_editor.get_config()
        label  = " / ".join(lay.name for lay in config.layers)
        self.plot_panel.set_unwrap(self.ui.chk_unwrap.isChecked())
        self.plot_panel.plot(
            self._last_lam, amp, R, phi, amp_t, T_t, phi_t,
            label=label, clear=True,
        )

    @Slot(bool)
    def _on_na_toggle(self, checked: bool) -> None:
        self.ui.edit_angle.setEnabled(not checked)
        self.ui.radio_pol_both.setVisible(checked)
        if not checked and self.ui.radio_pol_both.isChecked():
            self.ui.radio_pol_s.setChecked(True)
        self._schedule_recompute()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_pol(self) -> str:
        if self.ui.radio_pol_p.isChecked():
            return "p"
        if self.ui.radio_pol_both.isChecked():
            return "both"
        return "s"

    def _current_angle(self) -> float:
        try:
            return float(self.ui.edit_angle.text())
        except ValueError:
            return 0.0

    @Slot(str)
    def _set_status(self, msg: str) -> None:
        self.ui.lbl_status.setText(msg)

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    @Slot()
    def _open_stack(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open stack", "", "JSON (*.json);;All (*.*)"
        )
        if not path:
            return
        try:
            config = StackConfig.load(path)
            self.stack_editor.set_config(config)
            self._schedule_recompute()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    @Slot()
    def _save_stack(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save stack", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            self.stack_editor.get_config().save(path)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    @Slot()
    def _export_csv(self) -> None:
        if self._last_r is None and self._last_R_eff is None:
            QMessageBox.information(self, "Export", "Compute a spectrum first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            if self._last_mode == "na" and self._last_R_eff is not None:
                if self._last_T_eff is not None:
                    w.writerow(["lambda_nm", "R_eff", "T_eff"])
                    for row in zip(self._last_lam, self._last_R_eff, self._last_T_eff):
                        w.writerow([f"{v:.6g}" for v in row])
                else:
                    w.writerow(["lambda_nm", "R_eff"])
                    for row in zip(self._last_lam, self._last_R_eff):
                        w.writerow([f"{v:.6g}" for v in row])
            else:
                pol   = self._current_pol()
                angle = self._current_angle()
                amp, R, phi = r_to_observables(self._last_r)
                if self._last_t is not None:
                    amp_t, T_t, phi_t = t_to_observables(
                        self._last_t, self._last_N0_arr, self._last_Ns_arr, angle, pol
                    )
                    w.writerow(["lambda_nm", "|r|", "R", "phi_r_rad", "|t|", "T", "phi_t_rad"])
                    for row in zip(self._last_lam, amp, R, phi, amp_t, T_t, phi_t):
                        w.writerow([f"{v:.6g}" for v in row])
                else:
                    w.writerow(["lambda_nm", "|r|", "R", "phi_rad"])
                    for row in zip(self._last_lam, amp, R, phi):
                        w.writerow([f"{v:.6g}" for v in row])
        self._set_status(f"CSV saved: {Path(path).name}")

    @Slot()
    def _export_png(self) -> None:
        if self._last_r is None and self._last_R_eff is None:
            QMessageBox.information(self, "Export", "Compute a spectrum first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PNG", "", "PNG (*.png)"
        )
        if not path:
            return
        try:
            self._render_png(path)
            self._set_status(f"PNG saved: {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Export error", str(exc))

    def _render_png(self, path: str) -> None:
        """Render the current result to a matplotlib figure and save as PNG."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 2, figsize=(11, 7), facecolor=BG_DARK)
        fig.subplots_adjust(hspace=0.06, wspace=0.32,
                            left=0.08, right=0.97, top=0.93, bottom=0.08)

        def _style(ax, ylabel, xlabel="", bottom=False):
            ax.set_facecolor(AX_BG)
            ax.tick_params(colors=TICK_COL, labelsize=8, direction="in", length=4)
            ax.yaxis.label.set_color(LABEL_COL)
            ax.xaxis.label.set_color(LABEL_COL)
            ax.set_ylabel(ylabel, fontsize=9)
            if bottom:
                ax.set_xlabel(xlabel, fontsize=9)
            else:
                ax.tick_params(labelbottom=False)
            ax.grid(color="#2a2a4a", linewidth=0.5, linestyle="--", alpha=0.7)
            for spine in ax.spines.values():
                spine.set_color(SPINE_COL)
                spine.set_linewidth(0.8)

        ax_r,  ax_t   = axes[0]
        ax_R,  ax_T   = axes[1]
        ax_phi, ax_phi_t = axes[2]

        _style(ax_r,   "|r|")
        _style(ax_t,   "|t|")
        _style(ax_R,   "R = |r|\u00b2")
        _style(ax_T,   "T")
        _style(ax_phi,   "\u03c6\u1d63 (rad)", xlabel="Wavelength (nm)", bottom=True)
        _style(ax_phi_t, "\u03c6\u209c (rad)", xlabel="Wavelength (nm)", bottom=True)

        ax_r.set_title("Reflection",   color=LABEL_COL, fontsize=9, pad=4)
        ax_t.set_title("Transmission", color=LABEL_COL, fontsize=9, pad=4)

        lam = self._last_lam
        col = PALETTE[0]

        if self._last_mode == "na" and self._last_R_eff is not None:
            ax_R.plot(lam, self._last_R_eff, color=col, lw=1.4)
            if self._last_T_eff is not None:
                ax_T.plot(lam, self._last_T_eff, color=col, lw=1.4)
            for ax, msg in [
                (ax_r,     "|r| \u2014 N/A"),
                (ax_phi,   "\u03c6\u1d63 \u2014 N/A"),
                (ax_t,     "|t| \u2014 N/A"),
                (ax_phi_t, "\u03c6\u209c \u2014 N/A"),
            ]:
                ax.text(0.5, 0.5, msg, transform=ax.transAxes,
                        ha="center", va="center", color=TICK_COL,
                        fontsize=8, style="italic")
        elif self._last_r is not None:
            pol   = self._current_pol()
            angle = self._current_angle()
            amp, R, phi = r_to_observables(self._last_r)
            phi_plot = np.unwrap(phi) if self.ui.chk_unwrap.isChecked() else phi

            ax_r.plot(lam, amp, color=col, lw=1.4)
            ax_R.plot(lam, R,   color=col, lw=1.4)
            ax_phi.plot(lam, phi_plot, color=col, lw=1.4)

            if self._last_t is not None:
                amp_t, T_t, phi_t = t_to_observables(
                    self._last_t, self._last_N0_arr, self._last_Ns_arr, angle, pol
                )
                phi_t_plot = np.unwrap(phi_t) if self.ui.chk_unwrap.isChecked() else phi_t
                ax_t.plot(lam, amp_t,       color=col, lw=1.4)
                ax_T.plot(lam, T_t,         color=col, lw=1.4)
                ax_phi_t.plot(lam, phi_t_plot, color=col, lw=1.4)

        fig.savefig(path, dpi=300, facecolor=BG_DARK)
        plt.close(fig)

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        self._thread.quit()
        self._thread.wait(3000)
        super().closeEvent(event)
