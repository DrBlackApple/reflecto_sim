"""Main Tkinter application window — controller wiring all components."""

from __future__ import annotations

import copy
import csv
import math
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np

from ..materials import MaterialLibrary, MaterialRangeError
from ..stack import StackConfig, resolve_stack, build_N_matrix
from ..tmm import compute_spectrum, compute_na_spectrum, r_to_observables, warm_up_jit
from .plot_panel import PlotPanel, BG_DARK, LABEL_COL, TICK_COL, SPINE_COL, AX_BG

_BTN_BG = "#1e1e3a"
_BTN_FG = "#ccccee"
_ENTRY_BG = "#1a1a2e"

_DEBOUNCE_MS = 250  # ms before auto-recompute triggers


def _label(parent, text, **kw):
    kw.setdefault("font", ("Consolas", 9))
    return tk.Label(parent, text=text, bg=BG_DARK, fg=LABEL_COL, **kw)


def _entry(parent, var, width=8):
    return tk.Entry(
        parent,
        textvariable=var,
        width=width,
        bg=_ENTRY_BG,
        fg=LABEL_COL,
        insertbackground=LABEL_COL,
        relief=tk.FLAT,
        font=("Consolas", 9),
    )


class ReflectoApp(tk.Tk):
    """Top-level application window."""

    def __init__(self, lib: MaterialLibrary):
        super().__init__()
        self.lib = lib
        self.title("reflecto_sim — Reflectometry Simulator")
        self.configure(bg=BG_DARK)
        self.minsize(1200, 640)

        # ttk style for dark theme
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground=_ENTRY_BG,
            background=_ENTRY_BG,
            foreground=LABEL_COL,
            arrowcolor=LABEL_COL,
            selectbackground=_ENTRY_BG,
            selectforeground=LABEL_COL,
        )
        style.map("TCombobox", fieldbackground=[("readonly", _ENTRY_BG)])

        self._debounce_id: str | None = None
        self._computing = False
        self._last_r: np.ndarray | None = None
        self._last_lam: np.ndarray | None = None
        self._last_R_eff: np.ndarray | None = None
        self._last_mode: str = "spectrum"  # "spectrum" | "na" | "sweep"

        self._build_ui()

        # Warm up Numba JIT in background
        threading.Thread(target=self._warmup, daemon=True).start()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        from .stack_editor import StackEditor

        mat_keys = list(self.lib.available())

        # ---- Menu bar ----
        menubar = tk.Menu(
            self,
            bg=BG_DARK,
            fg=LABEL_COL,
            activebackground=SPINE_COL,
            activeforeground=LABEL_COL,
        )
        file_menu = tk.Menu(
            menubar,
            tearoff=0,
            bg=BG_DARK,
            fg=LABEL_COL,
            activebackground=SPINE_COL,
            activeforeground=LABEL_COL,
        )
        file_menu.add_command(label="Open stack…", command=self._open_stack)
        file_menu.add_command(label="Save stack…", command=self._save_stack)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        # ---- Three-column layout ----
        main = tk.Frame(self, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)

        # Left column: stack editor
        left = tk.Frame(main, bg=BG_DARK, width=440)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(6, 0))
        left.pack_propagate(False)

        _label(left, "Stack Editor", font=("Consolas", 10, "bold")).pack(
            anchor="w", pady=(8, 2), padx=6
        )

        self.stack_editor = StackEditor(
            left,
            materials=mat_keys,
            on_change=self._schedule_recompute,
        )
        self.stack_editor.pack(fill=tk.BOTH, expand=True)

        # Centre: plot panel
        centre = tk.Frame(main, bg=BG_DARK)
        centre.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)

        self.plot_panel = PlotPanel(centre)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)

        # Right column: controls
        right = tk.Frame(main, bg=BG_DARK, width=200)
        right.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        right.pack_propagate(False)

        self._build_controls(right)

    def _build_controls(self, parent):
        pad = {"padx": 8, "pady": 3}

        _label(parent, "Simulation", font=("Consolas", 10, "bold")).pack(
            anchor="w", **pad
        )

        sep = tk.Frame(parent, bg=SPINE_COL, height=1)
        sep.pack(fill=tk.X, padx=8, pady=4)

        def row(label_text, widget):
            f = tk.Frame(parent, bg=BG_DARK)
            f.pack(fill=tk.X, **pad)
            _label(f, label_text, width=14, anchor="e").pack(side=tk.LEFT)
            widget(f).pack(side=tk.LEFT, padx=4)

        # Wavelength range
        self._lam_min = tk.StringVar(value="430")
        self._lam_max = tk.StringVar(value="1600")
        self._lam_step = tk.StringVar(value="1")
        row("λ min (nm):", lambda f: _entry(f, self._lam_min))
        row("λ max (nm):", lambda f: _entry(f, self._lam_max))
        row("Step (nm):", lambda f: _entry(f, self._lam_step))

        for v in (self._lam_min, self._lam_max, self._lam_step):
            v.trace_add("write", lambda *_: self._schedule_recompute())

        sep2 = tk.Frame(parent, bg=SPINE_COL, height=1)
        sep2.pack(fill=tk.X, padx=8, pady=4)

        # Angle and polarisation
        self._angle = tk.StringVar(value="0")
        self._angle.trace_add("write", lambda *_: self._schedule_recompute())
        angle_row = tk.Frame(parent, bg=BG_DARK)
        angle_row.pack(fill=tk.X, **pad)
        _label(angle_row, "Angle (°):", width=14, anchor="e").pack(side=tk.LEFT)
        self._angle_entry = _entry(angle_row, self._angle)
        self._angle_entry.pack(side=tk.LEFT, padx=4)

        self._pol = tk.StringVar(value="s")
        pol_frame = tk.Frame(parent, bg=BG_DARK)
        pol_frame.pack(fill=tk.X, **pad)
        _label(pol_frame, "Polarisation:", width=14, anchor="e").pack(side=tk.LEFT)
        for p in ("s", "p"):
            tk.Radiobutton(
                pol_frame,
                text=p,
                variable=self._pol,
                value=p,
                bg=BG_DARK,
                fg=LABEL_COL,
                selectcolor=AX_BG,
                activebackground=BG_DARK,
                font=("Consolas", 9),
                command=self._schedule_recompute,
            ).pack(side=tk.LEFT, padx=2)
        # "both (unpol)" — shown only when NA mode is active
        self._pol_both_btn = tk.Radiobutton(
            pol_frame,
            text="both",
            variable=self._pol,
            value="both",
            bg=BG_DARK,
            fg=LABEL_COL,
            selectcolor=AX_BG,
            activebackground=BG_DARK,
            font=("Consolas", 9),
            command=self._schedule_recompute,
        )
        # not packed yet — revealed by _on_na_toggle

        sep3 = tk.Frame(parent, bg=SPINE_COL, height=1)
        sep3.pack(fill=tk.X, padx=8, pady=4)

        # Phase unwrap
        self._unwrap = tk.BooleanVar(value=False)
        uw_chk = tk.Checkbutton(
            parent,
            text="Unwrap phase",
            variable=self._unwrap,
            bg=BG_DARK,
            fg=LABEL_COL,
            selectcolor=AX_BG,
            activebackground=BG_DARK,
            font=("Consolas", 9),
            command=self._on_unwrap_toggle,
        )
        uw_chk.pack(anchor="w", padx=12)

        self._autofit = tk.BooleanVar(value=False)
        tk.Checkbutton(
            parent,
            text="Autofit Y",
            variable=self._autofit,
            bg=BG_DARK,
            fg=LABEL_COL,
            selectcolor=AX_BG,
            activebackground=BG_DARK,
            font=("Consolas", 9),
            command=self._on_autofit_toggle,
        ).pack(anchor="w", padx=12)

        self._log_y = tk.BooleanVar(value=False)
        tk.Checkbutton(
            parent,
            text="Log Y",
            variable=self._log_y,
            bg=BG_DARK,
            fg=LABEL_COL,
            selectcolor=AX_BG,
            activebackground=BG_DARK,
            font=("Consolas", 9),
            command=self._on_log_y_toggle,
        ).pack(anchor="w", padx=12)

        sep4 = tk.Frame(parent, bg=SPINE_COL, height=1)
        sep4.pack(fill=tk.X, padx=8, pady=8)

        # Objective (NA integration)
        _label(parent, "Objective", font=("Consolas", 9, "bold")).pack(
            anchor="w", padx=8
        )

        sep_obj = tk.Frame(parent, bg=SPINE_COL, height=1)
        sep_obj.pack(fill=tk.X, padx=8, pady=2)

        self._na = tk.StringVar(value="0.0")
        self._na.trace_add("write", lambda *_: self._schedule_recompute())
        row("NA:", lambda f: _entry(f, self._na))

        self._magnif = tk.StringVar(value="10")
        row("Magnif. (×):", lambda f: _entry(f, self._magnif))

        self._use_na = tk.BooleanVar(value=False)
        tk.Checkbutton(
            parent,
            text="Use NA integration",
            variable=self._use_na,
            bg=BG_DARK,
            fg=LABEL_COL,
            selectcolor=AX_BG,
            activebackground=BG_DARK,
            font=("Consolas", 9),
            command=self._on_na_toggle,
        ).pack(anchor="w", padx=12)

        sep5 = tk.Frame(parent, bg=SPINE_COL, height=1)
        sep5.pack(fill=tk.X, padx=8, pady=8)

        # Compute button
        tk.Button(
            parent,
            text="▶  Compute",
            command=self._compute,
            bg="#1a3a1a",
            fg="#98FB98",
            relief=tk.FLAT,
            font=("Consolas", 10, "bold"),
            padx=10,
            pady=4,
        ).pack(fill=tk.X, padx=8, pady=2)

        tk.Button(
            parent,
            text="Clear plot",
            command=self.plot_panel.clear,
            bg=_BTN_BG,
            fg=_BTN_FG,
            relief=tk.FLAT,
            font=("Consolas", 9),
            padx=10,
        ).pack(fill=tk.X, padx=8, pady=2)

        sep5 = tk.Frame(parent, bg=SPINE_COL, height=1)
        sep5.pack(fill=tk.X, padx=8, pady=8)

        # Export
        _label(parent, "Export:").pack(anchor="w", padx=8)
        tk.Button(
            parent,
            text="Save CSV",
            command=self._export_csv,
            bg=_BTN_BG,
            fg=_BTN_FG,
            relief=tk.FLAT,
            font=("Consolas", 9),
            padx=10,
        ).pack(fill=tk.X, padx=8, pady=2)
        tk.Button(
            parent,
            text="Save PNG",
            command=self._export_png,
            bg=_BTN_BG,
            fg=_BTN_FG,
            relief=tk.FLAT,
            font=("Consolas", 9),
            padx=10,
        ).pack(fill=tk.X, padx=8, pady=2)

        # Status label at bottom
        self._status_var = tk.StringVar(value="Ready")
        tk.Label(
            parent,
            textvariable=self._status_var,
            bg=BG_DARK,
            fg=TICK_COL,
            font=("Consolas", 8),
            wraplength=180,
            justify=tk.LEFT,
        ).pack(anchor="w", padx=8, pady=(12, 0))

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    def _schedule_recompute(self):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(_DEBOUNCE_MS, self._compute)

    def _compute(self):
        if self._computing:
            return
        try:
            lam_min = float(self._lam_min.get())
            lam_max = float(self._lam_max.get())
            lam_step = float(self._lam_step.get())
            theta = float(self._angle.get())
        except ValueError:
            self._status("Invalid parameter values.")
            return

        if lam_min >= lam_max or lam_step <= 0:
            self._status("Invalid wavelength range.")
            return

        use_na = self._use_na.get()
        na_val = 0.0
        if use_na:
            try:
                na_val = float(self._na.get())
            except ValueError:
                self._status("Invalid NA value.")
                return
            if na_val <= 0.0:
                use_na = False

        lam_array = np.arange(lam_min, lam_max + lam_step * 0.5, lam_step)
        config = self.stack_editor.get_config()

        if not config.layers:
            self._status("Add at least one layer to compute.")
            return

        # Route to sweep if any layer has sweep_mode configured
        for i, layer in enumerate(config.layers):
            if layer.sweep_mode == "material" and len(layer.sweep_materials) >= 2:
                self._run_sweep({"layer_index": i, "materials": layer.sweep_materials})
                return
            if layer.sweep_mode == "mix" and layer.sweep_mat_b:
                self._run_mix_sweep(
                    {
                        "layer_index": i,
                        "mat_a": layer.material,
                        "mat_b": layer.sweep_mat_b,
                        "model": layer.sweep_mix_model,
                        "f_values": np.linspace(0.0, 1.0, layer.sweep_n_pts).tolist(),
                    }
                )
                return

        self._computing = True
        self._status("Computing…")
        pol = self._pol.get()

        def worker():
            try:
                layers, N0_arr, Ns_arr = resolve_stack(config, lam_array, self.lib)
                N_mat, d_arr = build_N_matrix(layers)
                if use_na:
                    R_eff = compute_na_spectrum(
                        N_mat,
                        d_arr,
                        lam_array,
                        N0_arr,
                        Ns_arr,
                        na=na_val,
                        pol=pol,
                    )
                    n0_ref = N0_arr[len(N0_arr) // 2].real
                    theta_max_deg = math.degrees(math.asin(na_val / n0_ref))
                    self.after(
                        0,
                        lambda: self._update_na_plot(
                            lam_array, R_eff, na_val, theta_max_deg
                        ),
                    )
                else:
                    r = compute_spectrum(
                        N_mat,
                        d_arr,
                        lam_array,
                        N0_arr,
                        Ns_arr,
                        theta_deg=theta,
                        pol=pol,
                    )
                    amp, R, phi = r_to_observables(r)
                    self._last_r = r
                    self._last_lam = lam_array
                    self.after(0, lambda: self._update_plot(lam_array, amp, R, phi))
            except MaterialRangeError as e:
                self.after(0, lambda: self._status(f"Range error: {e}"))
            except Exception as e:
                self.after(0, lambda: self._status(f"Error: {e}"))
            finally:
                self._computing = False

        threading.Thread(target=worker, daemon=True).start()

    def _update_plot(self, lam, amp, R, phi):
        config = self.stack_editor.get_config()
        label = " / ".join(l.name for l in config.layers)
        self.plot_panel.set_unwrap(self._unwrap.get())
        self.plot_panel.plot(lam, amp, R, phi, label=label, clear=True)
        r_single = amp[len(amp) // 2]
        R_single = R[len(R) // 2]
        lam_mid = lam[len(lam) // 2]
        self._status(
            f"Done — {len(lam)} pts\n"
            f"@{lam_mid:.0f}nm: |r|={r_single:.3f} R={R_single:.3f}"
        )

    def _on_unwrap_toggle(self):
        self._replot_last()

    def _on_autofit_toggle(self):
        self.plot_panel.set_autofit(self._autofit.get())
        self._replot_last()

    def _on_log_y_toggle(self):
        self.plot_panel.set_log_y(self._log_y.get())
        self._replot_last()

    def _replot_last(self):
        """Re-draw the last single spectrum with current display settings."""
        if self._last_r is not None:
            from ..tmm import r_to_observables

            amp, R, phi = r_to_observables(self._last_r)
            config = self.stack_editor.get_config()
            label = " / ".join(l.name for l in config.layers)
            self.plot_panel.set_unwrap(self._unwrap.get())
            self.plot_panel.plot(self._last_lam, amp, R, phi, label=label, clear=True)

    def _on_na_toggle(self):
        if self._use_na.get():
            self._angle_entry.config(state=tk.DISABLED)
            self._pol_both_btn.pack(side=tk.LEFT, padx=2)
        else:
            self._angle_entry.config(state=tk.NORMAL)
            self._pol_both_btn.pack_forget()
            if self._pol.get() == "both":
                self._pol.set("s")
        self._schedule_recompute()

    def _update_na_plot(self, lam, R_eff, na_val, theta_max_deg):
        self._last_R_eff = R_eff
        self._last_lam = lam
        self._last_mode = "na"
        self._last_r = None
        label = f"NA={na_val:.2f}"
        self.plot_panel.plot_na_result(lam, R_eff, label=label)
        self._status(
            f"Done — NA={na_val:.2f}  θmax={theta_max_deg:.1f}°\n" f"{len(lam)} pts"
        )

    def _run_sweep(self, params: dict):
        if self._computing:
            return
        try:
            lam_min = float(self._lam_min.get())
            lam_max = float(self._lam_max.get())
            lam_step = float(self._lam_step.get())
            theta = float(self._angle.get())
        except ValueError:
            self._status("Invalid parameter values.")
            return

        lam_array = np.arange(lam_min, lam_max + lam_step * 0.5, lam_step)
        base_config = self.stack_editor.get_config()
        layer_idx = params["layer_index"]
        materials = params["materials"]
        pol = self._pol.get() if self._pol.get() != "both" else "s"

        self._computing = True
        self._status(f"Sweep: 0/{len(materials)}…")

        def worker():
            results = []
            errors = []
            for mat in materials:
                try:
                    cfg = copy.deepcopy(base_config)
                    cfg.layers[layer_idx].material = mat
                    layers, N0_arr, Ns_arr = resolve_stack(cfg, lam_array, self.lib)
                    N_mat, d_arr = build_N_matrix(layers)
                    r = compute_spectrum(
                        N_mat,
                        d_arr,
                        lam_array,
                        N0_arr,
                        Ns_arr,
                        theta_deg=theta,
                        pol=pol,
                    )
                    amp, R, phi = r_to_observables(r)
                    results.append((mat, lam_array, amp, R, phi))
                except MaterialRangeError:
                    errors.append(mat)
                except Exception:
                    errors.append(mat)
            self.after(0, lambda: self._update_sweep_plot(results, errors))
            self._computing = False

        threading.Thread(target=worker, daemon=True).start()

    def _update_sweep_plot(self, results: list, errors: list):
        if not results:
            self._status("Sweep: no valid materials.")
            return
        self.plot_panel.clear()
        for i, (mat, lam, amp, R, phi) in enumerate(results):
            self.plot_panel.plot(lam, amp, R, phi, label=mat, color_idx=i, clear=False)
        # Store first curve for hover / export
        self._last_r = None
        self._last_lam = results[0][1]
        self._last_mode = "sweep"
        msg = f"Sweep: {len(results)} materials"
        if errors:
            msg += f" ({len(errors)} range errors: {', '.join(errors[:3])})"
        self._status(msg)

    def _run_mix_sweep(self, params: dict):
        if self._computing:
            return
        try:
            lam_min = float(self._lam_min.get())
            lam_max = float(self._lam_max.get())
            lam_step = float(self._lam_step.get())
            theta = float(self._angle.get())
        except ValueError:
            self._status("Invalid parameter values.")
            return

        lam_array = np.arange(lam_min, lam_max + lam_step * 0.5, lam_step)
        base_config = self.stack_editor.get_config()
        layer_idx = params["layer_index"]
        mat_a = params["mat_a"]
        mat_b = params["mat_b"]
        model = params["model"]
        f_values = params["f_values"]
        pol = self._pol.get() if self._pol.get() != "both" else "s"

        self._computing = True
        self._status(f"Mix sweep: 0/{len(f_values)}…")

        def worker():
            results = []
            errors = []
            for f in f_values:
                try:
                    cfg = copy.deepcopy(base_config)
                    layer = cfg.layers[layer_idx]
                    layer.material = mat_a
                    layer.mix_mat_b = mat_b
                    layer.mix_f = float(f)
                    layer.mix_model = model
                    layers, N0_arr, Ns_arr = resolve_stack(cfg, lam_array, self.lib)
                    N_mat, d_arr = build_N_matrix(layers)
                    r = compute_spectrum(
                        N_mat,
                        d_arr,
                        lam_array,
                        N0_arr,
                        Ns_arr,
                        theta_deg=theta,
                        pol=pol,
                    )
                    amp, R, phi = r_to_observables(r)
                    results.append((float(f), lam_array, amp, R, phi))
                except MaterialRangeError:
                    errors.append(f)
                except Exception:
                    errors.append(f)
            self.after(
                0, lambda: self._update_mix_sweep_plot(results, errors, mat_a, mat_b)
            )
            self._computing = False

        threading.Thread(target=worker, daemon=True).start()

    def _update_mix_sweep_plot(
        self, results: list, errors: list, mat_a: str, mat_b: str
    ):
        import matplotlib

        if not results:
            self._status("Mix sweep: no valid points.")
            return
        cmap = matplotlib.colormaps.get_cmap("plasma")
        self.plot_panel.clear()
        for f, lam, amp, R, phi in results:
            rgba = cmap(f)
            col = "#{:02x}{:02x}{:02x}".format(
                int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255)
            )
            self.plot_panel.plot(lam, amp, R, phi, color=col, clear=False)
        self.plot_panel.add_colorbar("plasma", 0.0, 1.0, f"f  ({mat_a} → {mat_b})")
        self._last_r = None
        self._last_lam = results[0][1]
        self._last_mode = "sweep"
        msg = f"Mix sweep: {len(results)} pts  {mat_a} → {mat_b}"
        if errors:
            msg += f"  ({len(errors)} errors)"
        self._status(msg)

    def _status(self, msg: str):
        self._status_var.set(msg)

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def _open_stack(self):
        path = filedialog.askopenfilename(
            title="Open stack", filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            config = StackConfig.load(path)
            self.stack_editor.set_config(config)
            self._schedule_recompute()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_stack(self):
        path = filedialog.asksaveasfilename(
            title="Save stack", defaultextension=".json", filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        try:
            self.stack_editor.get_config().save(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_csv(self):
        if self._last_r is None and self._last_R_eff is None:
            messagebox.showinfo("Export", "Compute a spectrum first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save CSV", defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            if self._last_mode == "na" and self._last_R_eff is not None:
                w.writerow(["lambda_nm", "R_eff"])
                for row in zip(self._last_lam, self._last_R_eff):
                    w.writerow([f"{v:.6g}" for v in row])
            else:
                amp, R, phi = r_to_observables(self._last_r)
                w.writerow(["lambda_nm", "|r|", "R", "phi_rad"])
                for row in zip(self._last_lam, amp, R, phi):
                    w.writerow([f"{v:.6g}" for v in row])
        self._status(f"CSV saved: {Path(path).name}")

    def _export_png(self):
        path = filedialog.asksaveasfilename(
            title="Save PNG", defaultextension=".png", filetypes=[("PNG", "*.png")]
        )
        if not path:
            return
        self.plot_panel.fig.savefig(
            path, dpi=300, facecolor=self.plot_panel.fig.get_facecolor()
        )
        self._status(f"PNG saved: {Path(path).name}")

    # ------------------------------------------------------------------
    # JIT warm-up
    # ------------------------------------------------------------------

    def _warmup(self):
        warm_up_jit()
        self.after(0, lambda: self._status("Ready (JIT compiled)"))
