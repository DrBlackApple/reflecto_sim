"""Matplotlib plot panel embedded in Tkinter — scientific dark theme."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# ---- Dark scientific palette ------------------------------------------------
BG_DARK = "#0d0d1a"
AX_BG = "#12122a"
GRID_COL = "#2a2a4a"
TICK_COL = "#aaaacc"
LABEL_COL = "#ccccee"
SPINE_COL = "#3a3a5a"
PALETTE = [
    "#00BFFF",
    "#FF6B6B",
    "#98FB98",
    "#FFD700",
    "#DA70D6",
    "#FF8C00",
    "#7FFFD4",
    "#FF69B4",
]


def _style_ax(ax, ylabel: str, xlabel: str = "", bottom: bool = False) -> None:
    ax.set_facecolor(AX_BG)
    ax.tick_params(colors=TICK_COL, labelsize=8, direction="in", length=4)
    ax.yaxis.label.set_color(LABEL_COL)
    ax.xaxis.label.set_color(LABEL_COL)
    ax.set_ylabel(ylabel, fontsize=9)
    if bottom:
        ax.set_xlabel(xlabel, fontsize=9)
    else:
        ax.tick_params(labelbottom=False)
    ax.grid(color=GRID_COL, linewidth=0.5, linestyle="--", alpha=0.7)
    for spine in ax.spines.values():
        spine.set_color(SPINE_COL)
        spine.set_linewidth(0.8)


class PlotPanel(tk.Frame):
    """Three-subplot panel: |r|(λ), R(λ), φ(λ) with hover crosshair."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)

        self.fig = Figure(figsize=(6, 7), facecolor=BG_DARK, tight_layout=True)
        self.fig.subplots_adjust(
            hspace=0.06, left=0.12, right=0.97, top=0.96, bottom=0.08
        )

        self.ax_r = self.fig.add_subplot(3, 1, 1)
        self.ax_R = self.fig.add_subplot(3, 1, 2)
        self.ax_phi = self.fig.add_subplot(3, 1, 3)

        _style_ax(self.ax_r, r"|r|", bottom=False)
        _style_ax(self.ax_R, r"R = |r|²", bottom=False)
        _style_ax(self.ax_phi, r"φ (rad)", xlabel="Wavelength (nm)", bottom=True)

        self.ax_r.set_ylim(0, 1.05)
        self.ax_R.set_ylim(0, 1.05)

        # Title
        self.fig.suptitle(
            "Reflectometry spectrum", color=LABEL_COL, fontsize=10, y=0.99
        )

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Minimal toolbar (save button, zoom)
        toolbar_frame = tk.Frame(self, bg=BG_DARK)
        toolbar_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.config(background=BG_DARK)
        for btn in self.toolbar.winfo_children():
            try:
                btn.config(background=BG_DARK, foreground=LABEL_COL)
            except Exception:
                pass
        self.toolbar.update()

        # Hover annotations
        self._vlines = []
        self._hover_labels: list[tk.Label] = []
        self._status_var = tk.StringVar(value="")
        status_bar = tk.Label(
            self,
            textvariable=self._status_var,
            anchor="w",
            bg=BG_DARK,
            fg=TICK_COL,
            font=("Consolas", 8),
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._on_leave)

        self._lam: np.ndarray | None = None
        self._amp: np.ndarray | None = None
        self._R: np.ndarray | None = None
        self._phi: np.ndarray | None = None
        self._unwrap = False
        self._autofit = False
        self._log_y = False
        self._colorbar = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plot(
        self,
        lam: np.ndarray,
        amp: np.ndarray,
        R: np.ndarray,
        phi: np.ndarray,
        label: str = "",
        color_idx: int = 0,
        clear: bool = True,
        color: str | None = None,
    ) -> None:
        """Update the three spectra plots."""
        self._lam = lam
        self._amp = amp
        self._R = R
        self._phi = phi

        col = color if color is not None else PALETTE[color_idx % len(PALETTE)]

        if clear:
            for ax in (self.ax_r, self.ax_R, self.ax_phi):
                ax.cla()
            _style_ax(self.ax_r, r"|r|", bottom=False)
            _style_ax(self.ax_R, r"R = |r|²", bottom=False)
            _style_ax(self.ax_phi, r"φ (rad)", xlabel="Wavelength (nm)", bottom=True)
            self.ax_r.set_ylim(0, 1.05)
            self.ax_R.set_ylim(0, 1.05)

        if clear:
            for ax in (self.ax_r, self.ax_R, self.ax_phi):
                ax.cla()
            _style_ax(self.ax_r, r"|r|", bottom=False)
            _style_ax(self.ax_R, r"R = |r|²", bottom=False)
            _style_ax(self.ax_phi, r"φ (rad)", xlabel="Wavelength (nm)", bottom=True)
            self._apply_yscale()

        phi_plot = np.unwrap(phi) if self._unwrap else phi

        self.ax_r.plot(lam, amp, color=col, lw=1.4, label=label if label else None)
        self.ax_R.plot(lam, R, color=col, lw=1.4)
        self.ax_phi.plot(lam, phi_plot, color=col, lw=1.4)

        if label:
            self.ax_r.legend(
                fontsize=7, facecolor=AX_BG, labelcolor=LABEL_COL, edgecolor=SPINE_COL
            )

        self.canvas.draw_idle()

    def _apply_yscale(self) -> None:
        """Apply log/linear scale and y-limits to |r| and R axes."""
        if self._log_y:
            self.ax_r.set_yscale("log")
            self.ax_R.set_yscale("log")
        else:
            self.ax_r.set_yscale("linear")
            self.ax_R.set_yscale("linear")
            if not self._autofit:
                self.ax_r.set_ylim(0, 1.05)
                self.ax_R.set_ylim(0, 1.05)

    def clear(self) -> None:
        if self._colorbar is not None:
            self._colorbar.remove()
            self._colorbar = None
            self.fig.subplots_adjust(
                hspace=0.06, left=0.12, right=0.97, top=0.96, bottom=0.08
            )
        for ax in (self.ax_r, self.ax_R, self.ax_phi):
            ax.cla()
        _style_ax(self.ax_r, r"|r|", bottom=False)
        _style_ax(self.ax_R, r"R = |r|²", bottom=False)
        _style_ax(self.ax_phi, r"φ (rad)", xlabel="Wavelength (nm)", bottom=True)
        self._apply_yscale()
        self.canvas.draw_idle()
        self._lam = None

    def set_unwrap(self, unwrap: bool) -> None:
        self._unwrap = unwrap

    def set_autofit(self, val: bool) -> None:
        self._autofit = val

    def set_log_y(self, val: bool) -> None:
        self._log_y = val

    def add_colorbar(
        self, cmap_name: str, vmin: float, vmax: float, label: str = ""
    ) -> None:
        """Add a vertical colorbar to the right of all three subplots."""
        import matplotlib
        from matplotlib.colors import Normalize

        if self._colorbar is not None:
            self._colorbar.remove()
            self._colorbar = None

        cmap = matplotlib.colormaps.get_cmap(cmap_name)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        self._colorbar = self.fig.colorbar(
            sm,
            ax=[self.ax_r, self.ax_R, self.ax_phi],
            label=label,
            pad=0.02,
            fraction=0.04,
            aspect=30,
        )
        self._colorbar.ax.yaxis.label.set_color(LABEL_COL)
        self._colorbar.ax.tick_params(colors=TICK_COL, labelsize=7)
        for spine in self._colorbar.ax.spines.values():
            spine.set_color(SPINE_COL)
        self.canvas.draw_idle()

    # ------------------------------------------------------------------
    # Hover
    # ------------------------------------------------------------------

    def plot_na_result(
        self,
        lam: np.ndarray,
        R_eff: np.ndarray,
        label: str = "",
        color_idx: int = 0,
        clear: bool = True,
    ) -> None:
        """Plot NA-integrated effective reflectance. Only the R panel is populated."""
        col = PALETTE[color_idx % len(PALETTE)]

        if clear:
            for ax in (self.ax_r, self.ax_R, self.ax_phi):
                ax.cla()
            _style_ax(self.ax_r, r"|r|", bottom=False)
            _style_ax(self.ax_R, r"R = |r|²", bottom=False)
            _style_ax(self.ax_phi, r"φ (rad)", xlabel="Wavelength (nm)", bottom=True)
            self._apply_yscale()
            for ax, msg in ((self.ax_r, "|r| — N/A (NA-integrated)"),
                            (self.ax_phi, "φ — N/A (NA-integrated)")):
                ax.text(0.5, 0.5, msg, transform=ax.transAxes,
                        ha="center", va="center", color=TICK_COL,
                        fontsize=8, style="italic")

        self.ax_R.plot(lam, R_eff, color=col, lw=1.4, label=label if label else None)
        if not self._log_y and not self._autofit:
            self.ax_R.set_ylim(0, 1.05)

        if label:
            self.ax_R.legend(
                fontsize=7, facecolor=AX_BG, labelcolor=LABEL_COL, edgecolor=SPINE_COL
            )

        # Store for hover (|r| approx = sqrt(R_eff), phase undefined)
        self._lam = lam
        self._R = R_eff
        self._amp = np.sqrt(np.clip(R_eff, 0, None))
        self._phi = np.zeros_like(R_eff)

        self.canvas.draw_idle()

    def _on_hover(self, event) -> None:
        if self._lam is None or event.inaxes is None:
            return
        if event.xdata is None:
            return
        # find nearest wavelength index
        idx = int(np.argmin(np.abs(self._lam - event.xdata)))
        lam_v = self._lam[idx]
        amp_v = self._amp[idx]
        R_v = self._R[idx]
        phi_v = self._phi[idx]
        self._status_var.set(
            f"λ = {lam_v:.1f} nm   |r| = {amp_v:.4f}   "
            f"R = {R_v:.4f}   φ = {phi_v:.4f} rad"
        )

        # Draw vertical crosshair on all axes
        for vl in self._vlines:
            try:
                vl.remove()
            except Exception:
                pass
        self._vlines = []
        for ax in (self.ax_r, self.ax_R, self.ax_phi):
            vl = ax.axvline(lam_v, color="#ffffff", lw=0.6, alpha=0.4, linestyle=":")
            self._vlines.append(vl)
        self.canvas.draw_idle()

    def _on_leave(self, event) -> None:
        for vl in self._vlines:
            try:
                vl.remove()
            except Exception:
                pass
        self._vlines = []
        self._status_var.set("")
        self.canvas.draw_idle()
