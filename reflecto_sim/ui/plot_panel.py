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


def _na_placeholder(ax, msg: str) -> None:
    ax.text(
        0.5,
        0.5,
        msg,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=TICK_COL,
        fontsize=8,
        style="italic",
    )


class PlotPanel(tk.Frame):
    """Six-subplot panel: reflection (|r|, R, φ_r) and transmission (|t|, T, φ_t)."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)

        self._lam: np.ndarray | None = None
        self._amp: np.ndarray | None = None
        self._R: np.ndarray | None = None
        self._phi: np.ndarray | None = None
        self._amp_t: np.ndarray | None = None
        self._T_t: np.ndarray | None = None
        self._phi_t: np.ndarray | None = None
        self._unwrap = False
        self._autofit = False
        self._log_y = False
        self._colorbar = None

        self.fig = Figure(figsize=(11, 7), facecolor=BG_DARK)
        self.fig.subplots_adjust(
            hspace=0.06, wspace=0.32, left=0.08, right=0.97, top=0.93, bottom=0.08
        )

        # Left column — reflection
        self.ax_r = self.fig.add_subplot(3, 2, 1)
        self.ax_R = self.fig.add_subplot(3, 2, 3, sharex=self.ax_r)
        self.ax_phi = self.fig.add_subplot(3, 2, 5, sharex=self.ax_r)

        # Right column — transmission
        self.ax_t = self.fig.add_subplot(3, 2, 2, sharex=self.ax_r)
        self.ax_T = self.fig.add_subplot(3, 2, 4, sharex=self.ax_r)
        self.ax_phi_t = self.fig.add_subplot(3, 2, 6, sharex=self.ax_r)

        self._style_all()

        # Column headers
        self.ax_r.set_title("Reflection", color=LABEL_COL, fontsize=9, pad=4)
        self.ax_t.set_title("Transmission", color=LABEL_COL, fontsize=9, pad=4)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    _SUBPLOT_ADJ = dict(
        hspace=0.06, wspace=0.32, left=0.08, right=0.97, top=0.93, bottom=0.08
    )

    def _style_all(self) -> None:
        _style_ax(self.ax_r, r"|r|", bottom=False)
        _style_ax(self.ax_R, r"R = |r|²", bottom=False)
        _style_ax(self.ax_phi, r"φ_r (rad)", xlabel="Wavelength (nm)", bottom=True)
        _style_ax(self.ax_t, r"|t|", bottom=False)
        _style_ax(self.ax_T, r"T", bottom=False)
        _style_ax(self.ax_phi_t, r"φ_t (rad)", xlabel="Wavelength (nm)", bottom=True)
        if self._colorbar is None:
            self.fig.subplots_adjust(**self._SUBPLOT_ADJ)
        self._apply_yscale()

    def _apply_yscale(self) -> None:
        for ax in (self.ax_r, self.ax_R, self.ax_t, self.ax_T):
            if self._log_y:
                ax.set_yscale("log")
            else:
                ax.set_yscale("linear")
                if not self._autofit:
                    ax.set_ylim(0, 1.05)

    def _all_axes(self):
        return (self.ax_r, self.ax_R, self.ax_phi, self.ax_t, self.ax_T, self.ax_phi_t)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plot(
        self,
        lam: np.ndarray,
        amp: np.ndarray,
        R: np.ndarray,
        phi: np.ndarray,
        amp_t: np.ndarray | None = None,
        T_t: np.ndarray | None = None,
        phi_t: np.ndarray | None = None,
        label: str = "",
        color_idx: int = 0,
        clear: bool = True,
        color: str | None = None,
    ) -> None:
        """Update all spectra plots."""
        self._lam = lam
        self._amp = amp
        self._R = R
        self._phi = phi
        self._amp_t = amp_t
        self._T_t = T_t
        self._phi_t = phi_t

        col = color if color is not None else PALETTE[color_idx % len(PALETTE)]

        if clear:
            for ax in self._all_axes():
                ax.cla()
            self._style_all()
            self.ax_r.set_title("Reflection", color=LABEL_COL, fontsize=9, pad=4)
            self.ax_t.set_title("Transmission", color=LABEL_COL, fontsize=9, pad=4)

        phi_plot = np.unwrap(phi) if self._unwrap else phi

        self.ax_r.plot(lam, amp, color=col, lw=1.4, label=label if label else None)
        self.ax_R.plot(lam, R, color=col, lw=1.4)
        self.ax_phi.plot(lam, phi_plot, color=col, lw=1.4)

        if amp_t is not None and T_t is not None and phi_t is not None:
            phi_t_plot = np.unwrap(phi_t) if self._unwrap else phi_t
            self.ax_t.plot(lam, amp_t, color=col, lw=1.4)
            self.ax_T.plot(lam, T_t, color=col, lw=1.4)
            self.ax_phi_t.plot(lam, phi_t_plot, color=col, lw=1.4)
        elif clear:
            _na_placeholder(self.ax_t, "|t| — N/A")
            _na_placeholder(self.ax_T, "T — N/A")
            _na_placeholder(self.ax_phi_t, "φ_t — N/A")

        if label:
            self.ax_r.legend(
                fontsize=7, facecolor=AX_BG, labelcolor=LABEL_COL, edgecolor=SPINE_COL
            )

        self.canvas.draw_idle()

    def plot_na_result(
        self,
        lam: np.ndarray,
        R_eff: np.ndarray,
        T_eff: np.ndarray | None = None,
        label: str = "",
        color_idx: int = 0,
        clear: bool = True,
    ) -> None:
        """Plot NA-integrated reflectance and transmittance."""
        col = PALETTE[color_idx % len(PALETTE)]

        if clear:
            for ax in self._all_axes():
                ax.cla()
            self._style_all()
            self.ax_r.set_title("Reflection", color=LABEL_COL, fontsize=9, pad=4)
            self.ax_t.set_title("Transmission", color=LABEL_COL, fontsize=9, pad=4)
            _na_placeholder(self.ax_r, "|r| — N/A (NA-integrated)")
            _na_placeholder(self.ax_phi, "φ_r — N/A (NA-integrated)")
            _na_placeholder(self.ax_t, "|t| — N/A (NA-integrated)")
            _na_placeholder(self.ax_phi_t, "φ_t — N/A (NA-integrated)")

        self.ax_R.plot(lam, R_eff, color=col, lw=1.4, label=label if label else None)
        if not self._log_y and not self._autofit:
            self.ax_R.set_ylim(0, 1.05)

        if T_eff is not None:
            self.ax_T.plot(lam, T_eff, color=col, lw=1.4)
            if not self._log_y and not self._autofit:
                self.ax_T.set_ylim(0, 1.05)
        else:
            if clear:
                _na_placeholder(self.ax_T, "T — N/A")

        if label:
            self.ax_R.legend(
                fontsize=7, facecolor=AX_BG, labelcolor=LABEL_COL, edgecolor=SPINE_COL
            )

        # Store for hover
        self._lam = lam
        self._R = R_eff
        self._amp = np.sqrt(np.clip(R_eff, 0, None))
        self._phi = np.zeros_like(R_eff)
        self._T_t = T_eff
        self._amp_t = np.sqrt(np.clip(T_eff, 0, None)) if T_eff is not None else None
        self._phi_t = np.zeros_like(T_eff) if T_eff is not None else None

        self.canvas.draw_idle()

    def clear(self) -> None:
        if self._colorbar is not None:
            self._colorbar.remove()
            self._colorbar = None
        for ax in self._all_axes():
            ax.cla()
        self._style_all()
        self.ax_r.set_title("Reflection", color=LABEL_COL, fontsize=9, pad=4)
        self.ax_t.set_title("Transmission", color=LABEL_COL, fontsize=9, pad=4)
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
        """Add a vertical colorbar to the right of all six subplots."""
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
            ax=list(self._all_axes()),
            label=label,
            pad=0.02,
            fraction=0.02,
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

    def _on_hover(self, event) -> None:
        if self._lam is None or event.inaxes is None:
            return
        if event.xdata is None:
            return
        idx = int(np.argmin(np.abs(self._lam - event.xdata)))
        lam_v = self._lam[idx]
        amp_v = self._amp[idx] if self._amp is not None else float("nan")
        R_v = self._R[idx] if self._R is not None else float("nan")
        phi_v = self._phi[idx] if self._phi is not None else float("nan")

        msg = (
            f"λ = {lam_v:.1f} nm   "
            f"|r| = {amp_v:.4f}   R = {R_v:.4f}   φ_r = {phi_v:.4f} rad"
        )

        if self._amp_t is not None:
            amp_t_v = self._amp_t[idx]
            T_v = self._T_t[idx] if self._T_t is not None else float("nan")
            phi_t_v = self._phi_t[idx] if self._phi_t is not None else float("nan")
            msg += f"   |t| = {amp_t_v:.4f}   T = {T_v:.4f}   φ_t = {phi_t_v:.4f} rad"

        self._status_var.set(msg)

        # Vertical crosshair on all axes
        for vl in self._vlines:
            try:
                vl.remove()
            except Exception:
                pass
        self._vlines = []
        for ax in self._all_axes():
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
