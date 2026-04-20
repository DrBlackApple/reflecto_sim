"""
PlotPanel — six-subplot pyqtgraph display panel.

Reflection column:   |r|(λ),  R(λ),    φ_r(λ)
Transmission column: |t|(λ),  T(λ),    φ_t(λ)

Interactive features
--------------------
* Linked X axes (zoom/pan all subplots together)
* Crosshair cursor showing values at mouse position
* Colourbar (7th column) for mix-fraction sweeps
* Log Y, Autofit Y, phase unwrapping
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from .palette import (
    AX_BG, BG_DARK, LABEL_COL, PALETTE, SPINE_COL, TICK_COL,
)
from .ui_compiled.ui_plot_panel import Ui_PlotPanel

# Re-export palette constants for backward-compat imports from app.py
__all__ = [
    "PlotPanel",
    "BG_DARK", "AX_BG", "LABEL_COL", "TICK_COL", "SPINE_COL", "PALETTE",
]


def _style_plot(pi: pg.PlotItem, ylabel: str, show_x: bool = False) -> None:
    """Apply dark scientific style to a PlotItem."""
    pi.getViewBox().setBackgroundColor(AX_BG)
    pi.showGrid(x=True, y=True, alpha=0.35)
    pi.setLabel("left", ylabel, color=LABEL_COL)
    for ax_name in ("left", "bottom", "top", "right"):
        ax = pi.getAxis(ax_name)
        ax.setPen(pg.mkPen(SPINE_COL))
        ax.setTextPen(pg.mkPen(TICK_COL))
    if not show_x:
        pi.getAxis("bottom").setStyle(showValues=False)
    else:
        pi.setLabel("bottom", "Wavelength (nm)", color=LABEL_COL)


class PlotPanel(QWidget):
    """Six-subplot pyqtgraph panel: reflection + transmission observables."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.ui = Ui_PlotPanel()
        self.ui.setupUi(self)

        self._unwrap  = False
        self._autofit = False
        self._log_y   = False

        # Stored data for hover and display-option re-renders
        self._lam:    np.ndarray | None = None
        self._amp:    np.ndarray | None = None
        self._R:      np.ndarray | None = None
        self._phi:    np.ndarray | None = None
        self._amp_t:  np.ndarray | None = None
        self._T_t:    np.ndarray | None = None
        self._phi_t:  np.ndarray | None = None

        self._colorbar_plot: pg.PlotItem | None = None

        self._setup_plots()
        self._setup_crosshair()
        self._setup_hover()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_plots(self) -> None:
        glw: pg.GraphicsLayoutWidget = self.ui.glw
        glw.setBackground(BG_DARK)
        glw.ci.layout.setSpacing(2)

        # Row 0
        self.pi_r   = glw.addPlot(row=0, col=0)
        self.pi_t   = glw.addPlot(row=0, col=1)
        # Row 1
        self.pi_R   = glw.addPlot(row=1, col=0)
        self.pi_T   = glw.addPlot(row=1, col=1)
        # Row 2
        self.pi_phi   = glw.addPlot(row=2, col=0)
        self.pi_phi_t = glw.addPlot(row=2, col=1)

        _style_plot(self.pi_r,     "|r|",        show_x=False)
        _style_plot(self.pi_t,     "|t|",        show_x=False)
        _style_plot(self.pi_R,     "R = |r|\u00b2", show_x=False)
        _style_plot(self.pi_T,     "T",           show_x=False)
        _style_plot(self.pi_phi,   "\u03c6\u1d63 (rad)", show_x=True)
        _style_plot(self.pi_phi_t, "\u03c6\u209c (rad)", show_x=True)

        # Column headers
        self.pi_r.setTitle("Reflection",    color=LABEL_COL)
        self.pi_t.setTitle("Transmission",  color=LABEL_COL)

        # Link all X axes to pi_r
        for pi in (self.pi_t, self.pi_R, self.pi_T, self.pi_phi, self.pi_phi_t):
            pi.setXLink(self.pi_r)

    def _all_plots(self) -> tuple[pg.PlotItem, ...]:
        return (
            self.pi_r, self.pi_t,
            self.pi_R, self.pi_T,
            self.pi_phi, self.pi_phi_t,
        )

    # ------------------------------------------------------------------
    # Crosshair
    # ------------------------------------------------------------------

    def _setup_crosshair(self) -> None:
        self._vlines: list[pg.InfiniteLine] = []
        for pi in self._all_plots():
            vl = pg.InfiniteLine(angle=90, movable=False,
                                 pen=pg.mkPen("#ffffff", width=0.6, style=Qt.DotLine))
            pi.addItem(vl, ignoreBounds=True)
            self._vlines.append(vl)

    def _restore_crosshairs(self) -> None:
        """Re-add crosshair lines after a pi.clear() call."""
        self._vlines = []
        for pi in self._all_plots():
            vl = pg.InfiniteLine(angle=90, movable=False,
                                 pen=pg.mkPen("#ffffff", width=0.6, style=Qt.DotLine))
            pi.addItem(vl, ignoreBounds=True)
            self._vlines.append(vl)

    def _move_crosshair(self, x: float) -> None:
        for vl in self._vlines:
            vl.setPos(x)

    # ------------------------------------------------------------------
    # Hover
    # ------------------------------------------------------------------

    def _setup_hover(self) -> None:
        self._proxy = pg.SignalProxy(
            self.ui.glw.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._on_mouse_move,
        )

    def _on_mouse_move(self, event) -> None:
        if self._lam is None:
            return
        pos = event[0]
        vb = self.pi_r.getViewBox()
        if not vb.sceneBoundingRect().contains(pos):
            # Try any plot
            for pi in self._all_plots():
                if pi.getViewBox().sceneBoundingRect().contains(pos):
                    vb = pi.getViewBox()
                    break
            else:
                return
        mouse_point = vb.mapSceneToView(pos)
        x = mouse_point.x()
        idx = int(np.argmin(np.abs(self._lam - x)))
        lam_v = self._lam[idx]
        self._move_crosshair(lam_v)

        parts = [f"\u03bb = {lam_v:.1f} nm"]
        if self._amp is not None:
            parts.append(f"|r| = {self._amp[idx]:.4f}")
        if self._R is not None:
            parts.append(f"R = {self._R[idx]:.4f}")
        if self._phi is not None:
            parts.append(f"\u03c6\u1d63 = {self._phi[idx]:.4f} rad")
        if self._amp_t is not None:
            parts.append(f"|t| = {self._amp_t[idx]:.4f}")
        if self._T_t is not None:
            parts.append(f"T = {self._T_t[idx]:.4f}")
        if self._phi_t is not None:
            parts.append(f"\u03c6\u209c = {self._phi_t[idx]:.4f} rad")
        self.ui.lbl_hover.setText("   ".join(parts))

    # ------------------------------------------------------------------
    # Y-scale helpers
    # ------------------------------------------------------------------

    def _apply_yscale(self) -> None:
        for pi in (self.pi_r, self.pi_R, self.pi_t, self.pi_T):
            if self._log_y:
                pi.setLogMode(False, True)
            else:
                pi.setLogMode(False, False)
                if not self._autofit:
                    pi.setYRange(0, 1.05, padding=0)
        if self._autofit or self._log_y:
            for pi in self._all_plots():
                pi.enableAutoRange(axis="y")

    def _na_placeholder(self, pi: pg.PlotItem, msg: str) -> None:
        ti = pg.TextItem(text=msg, color=TICK_COL, anchor=(0.5, 0.5))
        pi.addItem(ti)
        ti.setPos(
            sum(pi.getAxis("bottom").range) / 2 if pi.getAxis("bottom").range else 700,
            0.5,
        )

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
        """Plot one spectrum onto all six subplots."""
        col = color if color is not None else PALETTE[color_idx % len(PALETTE)]
        pen = pg.mkPen(col, width=1.4)

        if clear:
            self._clear_plots()

        # Store for hover / replot
        self._lam   = lam
        self._amp   = amp
        self._R     = R
        self._phi   = phi
        self._amp_t = amp_t
        self._T_t   = T_t
        self._phi_t = phi_t

        phi_plot = np.unwrap(phi) if self._unwrap else phi

        kw = dict(pen=pen, name=label) if label and clear else dict(pen=pen)
        self.pi_r.plot(lam, amp,      **kw)
        self.pi_R.plot(lam, R,        pen=pen)
        self.pi_phi.plot(lam, phi_plot, pen=pen)

        if amp_t is not None and T_t is not None and phi_t is not None:
            phi_t_plot = np.unwrap(phi_t) if self._unwrap else phi_t
            self.pi_t.plot(lam, amp_t,     pen=pen)
            self.pi_T.plot(lam, T_t,       pen=pen)
            self.pi_phi_t.plot(lam, phi_t_plot, pen=pen)
        elif clear:
            self._na_placeholder(self.pi_t,     "|t| \u2014 N/A")
            self._na_placeholder(self.pi_T,     "T \u2014 N/A")
            self._na_placeholder(self.pi_phi_t, "\u03c6\u209c \u2014 N/A")

        self._apply_yscale()

    def plot_na_result(
        self,
        lam: np.ndarray,
        R_eff: np.ndarray,
        T_eff: np.ndarray | None = None,
        label: str = "",
        color_idx: int = 0,
        clear: bool = True,
    ) -> None:
        """Plot NA-integrated reflectance/transmittance."""
        col = PALETTE[color_idx % len(PALETTE)]
        pen = pg.mkPen(col, width=1.4)

        if clear:
            self._clear_plots()
            self._na_placeholder(self.pi_r,     "|r| \u2014 N/A (NA-integrated)")
            self._na_placeholder(self.pi_phi,   "\u03c6\u1d63 \u2014 N/A (NA-integrated)")
            self._na_placeholder(self.pi_t,     "|t| \u2014 N/A (NA-integrated)")
            self._na_placeholder(self.pi_phi_t, "\u03c6\u209c \u2014 N/A (NA-integrated)")

        kw = dict(pen=pen, name=label) if label and clear else dict(pen=pen)
        self.pi_R.plot(lam, R_eff, **kw)
        if T_eff is not None:
            self.pi_T.plot(lam, T_eff, pen=pen)
        elif clear:
            self._na_placeholder(self.pi_T, "T \u2014 N/A")

        # Store for hover
        self._lam   = lam
        self._R     = R_eff
        self._amp   = np.sqrt(np.clip(R_eff, 0, None))
        self._phi   = np.zeros_like(R_eff)
        self._T_t   = T_eff
        self._amp_t = np.sqrt(np.clip(T_eff, 0, None)) if T_eff is not None else None
        self._phi_t = np.zeros_like(T_eff) if T_eff is not None else None

        self._apply_yscale()

    def clear(self) -> None:
        """Clear all plots and remove colorbar if present."""
        self._remove_colorbar()
        self._clear_plots()
        self._lam = None

    def _clear_plots(self) -> None:
        for pi in self._all_plots():
            pi.clear()
        # Re-apply style titles (clear() wipes them)
        self.pi_r.setTitle("Reflection",   color=LABEL_COL)
        self.pi_t.setTitle("Transmission", color=LABEL_COL)
        # Restore crosshairs that were removed by clear()
        self._restore_crosshairs()
        self._apply_yscale()

    def set_unwrap(self, val: bool) -> None:
        self._unwrap = val

    def set_autofit(self, val: bool) -> None:
        self._autofit = val
        self._apply_yscale()

    def set_log_y(self, val: bool) -> None:
        self._log_y = val
        self._apply_yscale()

    # ------------------------------------------------------------------
    # Colorbar for mix-fraction sweeps
    # ------------------------------------------------------------------

    def add_colorbar(
        self,
        cmap_name: str,
        vmin: float,
        vmax: float,
        label: str = "",
    ) -> None:
        """Add a vertical gradient colorbar in column 2, spanning all rows."""
        self._remove_colorbar()

        glw: pg.GraphicsLayoutWidget = self.ui.glw

        cb_plot = glw.addPlot(row=0, col=2, rowspan=3)
        cb_plot.setMaximumWidth(70)
        cb_plot.hideAxis("bottom")
        cb_plot.hideAxis("left")
        cb_plot.getViewBox().setBackgroundColor(AX_BG)

        # Build 1×256 gradient image
        n = 256
        gradient = np.linspace(0, 1, n, dtype=np.float32).reshape(1, n)
        img = pg.ImageItem(gradient)
        try:
            cmap = pg.colormap.get(cmap_name, source="matplotlib")
        except Exception:
            cmap = pg.colormap.get("plasma", source="matplotlib")
        img.setColorMap(cmap)
        cb_plot.addItem(img)

        # Right axis ticks: vmin at bottom (y=0), vmax at top (y=n-1)
        cb_plot.showAxis("right")
        ax = cb_plot.getAxis("right")
        tick_vals = [
            (0,       f"{vmin:.2f}"),
            (n // 2,  f"{(vmin + vmax) / 2:.2f}"),
            (n - 1,   f"{vmax:.2f}"),
        ]
        ax.setTicks([tick_vals])
        ax.setTextPen(pg.mkPen(TICK_COL))
        ax.setPen(pg.mkPen(SPINE_COL))
        if label:
            ax.setLabel(label, color=LABEL_COL)

        self._colorbar_plot = cb_plot

    def _remove_colorbar(self) -> None:
        if self._colorbar_plot is not None:
            self.ui.glw.removeItem(self._colorbar_plot)
            self._colorbar_plot = None
