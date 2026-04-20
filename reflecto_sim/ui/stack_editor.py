"""
Stack editor widget and dialogs — PySide6 rewrite.

StackEditor   — main widget (superstrate / layers / substrate)
LayerRowWidget — single layer row (inline, no .ui file — created dynamically)
MixedLayerDialog  — QDialog to configure a mixed-material layer
LayerSweepDialog  — QDialog to configure sweep mode for a layer
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..stack import LayerSpec, StackConfig
from .palette import AX_BG, BTN_BG, LABEL_COL, PALETTE, SPINE_COL, TICK_COL
from .ui_compiled.ui_stack_editor import Ui_StackEditor

_SEMI = ["air", "vacuum", "glass", "sio2", "bk7", "al2o3"]


def _swatch_color(idx: int) -> str:
    return PALETTE[idx % len(PALETTE)]


# ---------------------------------------------------------------------------
# LayerRowWidget — single layer, created purely in Python (dynamic)
# ---------------------------------------------------------------------------

class LayerRowWidget(QWidget):
    """One row in the layer list: swatch | name | material | thickness | sweep | ↑↓ | ×"""

    changed          = Signal()
    delete_requested = Signal(int)
    move_requested   = Signal(int, int)   # (index, delta: ±1)

    def __init__(
        self,
        spec: LayerSpec,
        index: int,
        materials: list[str],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._spec  = spec
        self._index = index

        hl = QHBoxLayout(self)
        hl.setContentsMargins(4, 2, 4, 2)
        hl.setSpacing(4)

        # Colour swatch
        swatch = QFrame()
        swatch.setFixedWidth(6)
        swatch.setStyleSheet(f"background: {_swatch_color(index)};")
        hl.addWidget(swatch)

        # Name
        self._edit_name = QLineEdit(spec.name)
        self._edit_name.setFixedWidth(88)
        self._edit_name.textChanged.connect(self._sync_name)
        hl.addWidget(self._edit_name)

        # Material
        self._combo_mat = QComboBox()
        self._combo_mat.addItems(materials)
        idx = self._combo_mat.findText(spec.material)
        if idx >= 0:
            self._combo_mat.setCurrentIndex(idx)
        else:
            self._combo_mat.setCurrentText(spec.material)
        self._combo_mat.setFixedWidth(120)
        self._combo_mat.currentTextChanged.connect(self._sync_material)
        hl.addWidget(self._combo_mat)

        # Thickness label + entry
        lbl_d = QLabel("d:")
        lbl_d.setFixedWidth(14)
        hl.addWidget(lbl_d)

        self._edit_thick = QLineEdit(str(spec.thickness_nm))
        self._edit_thick.setFixedWidth(60)
        self._edit_thick.setValidator(QDoubleValidator(0.0, 1e9, 4))
        self._edit_thick.textChanged.connect(self._sync_thickness)
        hl.addWidget(self._edit_thick)

        lbl_nm = QLabel("nm")
        lbl_nm.setFixedWidth(20)
        hl.addWidget(lbl_nm)

        # Sweep button
        self._btn_sweep = QPushButton(self._sweep_label())
        self._btn_sweep.setFixedWidth(30)
        self._btn_sweep.clicked.connect(self._open_sweep_config)
        self._refresh_sweep_btn()
        hl.addWidget(self._btn_sweep)

        hl.addStretch()

        # Move up/down
        btn_up = QPushButton("\u2191")
        btn_up.setFixedWidth(24)
        btn_up.clicked.connect(lambda: self.move_requested.emit(self._index, -1))
        hl.addWidget(btn_up)

        btn_down = QPushButton("\u2193")
        btn_down.setFixedWidth(24)
        btn_down.clicked.connect(lambda: self.move_requested.emit(self._index, +1))
        hl.addWidget(btn_down)

        # Delete
        btn_del = QPushButton("\u00d7")
        btn_del.setFixedWidth(24)
        btn_del.setStyleSheet("QPushButton { background: #3a0a0a; color: #ff8888; }")
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self._index))
        hl.addWidget(btn_del)

    # ------------------------------------------------------------------
    # Sync helpers
    # ------------------------------------------------------------------

    @Slot(str)
    def _sync_name(self, text: str) -> None:
        self._spec.name = text
        self.changed.emit()

    @Slot(str)
    def _sync_material(self, text: str) -> None:
        self._spec.material = text
        self.changed.emit()

    @Slot(str)
    def _sync_thickness(self, text: str) -> None:
        try:
            self._spec.thickness_nm = float(text)
            self.changed.emit()
        except ValueError:
            pass

    def update_materials(self, materials: list[str]) -> None:
        current = self._combo_mat.currentText()
        self._combo_mat.blockSignals(True)
        self._combo_mat.clear()
        self._combo_mat.addItems(materials)
        idx = self._combo_mat.findText(current)
        if idx >= 0:
            self._combo_mat.setCurrentIndex(idx)
        else:
            self._combo_mat.setCurrentText(current)
        self._combo_mat.blockSignals(False)

    # ------------------------------------------------------------------
    # Sweep button helpers
    # ------------------------------------------------------------------

    def _sweep_label(self) -> str:
        mode = self._spec.sweep_mode
        if mode == "material":
            return "\u2295M"
        if mode == "mix":
            return "\u2295X"
        return "\u2248"

    def _refresh_sweep_btn(self) -> None:
        mode = self._spec.sweep_mode
        if mode:
            self._btn_sweep.setStyleSheet(
                "QPushButton { background: #1a2a3a; color: #00BFFF; }"
            )
        else:
            self._btn_sweep.setStyleSheet(
                f"QPushButton {{ background: {BTN_BG}; color: {TICK_COL}; }}"
            )
        self._btn_sweep.setText(self._sweep_label())

    def _open_sweep_config(self) -> None:
        materials = [
            self._combo_mat.itemText(i) for i in range(self._combo_mat.count())
        ]
        dlg = LayerSweepDialog(self._spec, materials, parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.applied:
            self._refresh_sweep_btn()
            self.changed.emit()


# ---------------------------------------------------------------------------
# MixedLayerDialog
# ---------------------------------------------------------------------------

class MixedLayerDialog(QDialog):
    """Configure a mixed-material layer (Material A + B with volume fraction)."""

    def __init__(
        self,
        materials: list[str],
        existing: Optional[LayerSpec] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        from .ui_compiled.ui_mixed_layer_dialog import Ui_MixedLayerDialog
        from ..eff_medium import MODELS

        self.result: LayerSpec | None = None

        self.ui = Ui_MixedLayerDialog()
        self.ui.setupUi(self)

        # Populate combos
        self.ui.combo_mat_a.addItems(materials)
        self.ui.combo_mat_b.addItems(materials)
        self.ui.combo_model.addItems(list(MODELS.keys()))

        # Pre-fill if editing existing
        if existing:
            self.ui.edit_name.setText(existing.name)
            self.ui.combo_mat_a.setCurrentText(existing.material)
            self.ui.combo_mat_b.setCurrentText(existing.mix_mat_b or "")
            self.ui.slider_fraction.setValue(int(existing.mix_f * 100))
            self.ui.edit_thickness.setText(str(existing.thickness_nm))
            self.ui.combo_model.setCurrentText(existing.mix_model)
        else:
            self.ui.edit_name.setText("Mixed")
            if materials:
                self.ui.combo_mat_a.setCurrentIndex(0)
            if len(materials) > 1:
                self.ui.combo_mat_b.setCurrentIndex(1)

        # Slider → label sync
        self.ui.slider_fraction.valueChanged.connect(
            lambda v: self.ui.lbl_fraction_val.setText(f"{v / 100:.2f}")
        )

        # Override accept to validate first
        self.ui.button_box.accepted.disconnect()
        self.ui.button_box.accepted.connect(self._ok)

    def _ok(self) -> None:
        try:
            thick = float(self.ui.edit_thickness.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid thickness value.")
            return
        self.result = LayerSpec(
            name        = self.ui.edit_name.text(),
            material    = self.ui.combo_mat_a.currentText(),
            thickness_nm= thick,
            mix_mat_b   = self.ui.combo_mat_b.currentText(),
            mix_f       = self.ui.slider_fraction.value() / 100.0,
            mix_model   = self.ui.combo_model.currentText(),
        )
        self.accept()


# ---------------------------------------------------------------------------
# LayerSweepDialog
# ---------------------------------------------------------------------------

class LayerSweepDialog(QDialog):
    """Configure sweep mode (None / Material list / Mix fraction) for one layer."""

    def __init__(
        self,
        spec: LayerSpec,
        all_materials: list[str],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        from .ui_compiled.ui_layer_sweep_dialog import Ui_LayerSweepDialog
        from ..eff_medium import MODELS

        self.applied = False
        self._spec = spec

        self.ui = Ui_LayerSweepDialog()
        self.ui.setupUi(self)

        # Populate material list
        self.ui.list_materials.clear()
        for mat in all_materials:
            item = QListWidgetItem(mat)
            self.ui.list_materials.addItem(item)
            if mat in spec.sweep_materials:
                item.setSelected(True)

        # Mix combos
        self.ui.combo_mix_mat_b.addItems(all_materials)
        self.ui.combo_mix_model.addItems(list(MODELS.keys()))
        if spec.sweep_mat_b:
            self.ui.combo_mix_mat_b.setCurrentText(spec.sweep_mat_b)
        elif len(all_materials) > 1:
            self.ui.combo_mix_mat_b.setCurrentIndex(1)
        if spec.sweep_mix_model:
            self.ui.combo_mix_model.setCurrentText(spec.sweep_mix_model)
        self.ui.spin_n_pts.setValue(spec.sweep_n_pts or 20)

        # Update hint label
        self.ui.lbl_mix_hint.setText(f"(Mat A = {spec.material}, f=1)")

        # Set initial mode
        cur = spec.sweep_mode or "none"
        if cur == "material":
            self.ui.radio_material.setChecked(True)
        elif cur == "mix":
            self.ui.radio_mix.setChecked(True)
        else:
            self.ui.radio_none.setChecked(True)
        self._on_mode_changed()

        # Wire mode radios
        self.ui.radio_none.toggled.connect(lambda c: c and self._on_mode_changed())
        self.ui.radio_material.toggled.connect(lambda c: c and self._on_mode_changed())
        self.ui.radio_mix.toggled.connect(lambda c: c and self._on_mode_changed())

        # Select All / Clear buttons
        self.ui.btn_select_all.clicked.connect(
            lambda: self.ui.list_materials.selectAll()
        )
        self.ui.btn_clear_sel.clicked.connect(
            lambda: self.ui.list_materials.clearSelection()
        )

        # Override OK to validate
        self.ui.button_box.accepted.disconnect()
        self.ui.button_box.accepted.connect(self._apply)

    @Slot()
    def _on_mode_changed(self) -> None:
        if self.ui.radio_none.isChecked():
            self.ui.content_stack.setCurrentIndex(0)
        elif self.ui.radio_material.isChecked():
            self.ui.content_stack.setCurrentIndex(1)
        else:
            self.ui.content_stack.setCurrentIndex(2)

    @Slot()
    def _apply(self) -> None:
        if self.ui.radio_none.isChecked():
            self._spec.sweep_mode      = ""
            self._spec.sweep_materials = []
            self._spec.sweep_mat_b     = ""
        elif self.ui.radio_material.isChecked():
            selected = [
                item.text()
                for item in self.ui.list_materials.selectedItems()
            ]
            if len(selected) < 2:
                QMessageBox.warning(self, "Selection", "Select at least 2 materials.")
                return
            self._spec.sweep_mode      = "material"
            self._spec.sweep_materials = selected
        else:  # mix
            mat_b = self.ui.combo_mix_mat_b.currentText().strip()
            if not mat_b:
                QMessageBox.critical(self, "Error", "Select Material B.")
                return
            self._spec.sweep_mode      = "mix"
            self._spec.sweep_mat_b     = mat_b
            self._spec.sweep_mix_model = self.ui.combo_mix_model.currentText()
            self._spec.sweep_n_pts     = self.ui.spin_n_pts.value()
        self.applied = True
        self.accept()


# ---------------------------------------------------------------------------
# StackEditor — main widget
# ---------------------------------------------------------------------------

class StackEditor(QWidget):
    """Full stack editor: superstrate | layer list | substrate."""

    changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.ui = Ui_StackEditor()
        self.ui.setupUi(self)

        self._materials: list[str] = []
        self._config = StackConfig()
        self._rows: list[LayerRowWidget] = []

        # Populate boundary combos
        self.ui.combo_superstrate.addItems(_SEMI)
        self.ui.combo_substrate.addItems(_SEMI)

        self.ui.combo_superstrate.setCurrentText(self._config.superstrate)
        self.ui.combo_substrate.setCurrentText(self._config.substrate)

        self.ui.combo_superstrate.currentTextChanged.connect(self._sync_boundary)
        self.ui.combo_substrate.currentTextChanged.connect(self._sync_boundary)

        self.ui.btn_add_layer.clicked.connect(self._add_layer)
        self.ui.btn_add_mixed.clicked.connect(self._add_mixed)

    # ------------------------------------------------------------------
    # Boundary sync
    # ------------------------------------------------------------------

    @Slot()
    def _sync_boundary(self) -> None:
        self._config.superstrate = self.ui.combo_superstrate.currentText()
        self._config.substrate   = self.ui.combo_substrate.currentText()
        self.changed.emit()

    # ------------------------------------------------------------------
    # Layer management
    # ------------------------------------------------------------------

    def _rebuild_rows(self) -> None:
        # Remove existing rows (don't touch the trailing spacer)
        for row in self._rows:
            row.deleteLater()
        self._rows = []

        vl: QVBoxLayout = self.ui.layers_container.layout()
        # Insert rows before the trailing spacer (last item)
        for i, spec in enumerate(self._config.layers):
            row = LayerRowWidget(spec, i, self._materials)
            row.changed.connect(self.changed)
            row.delete_requested.connect(self._delete_layer)
            row.move_requested.connect(self._move_layer)
            # Insert before trailing spacer
            vl.insertWidget(vl.count() - 1, row)
            self._rows.append(row)

    @Slot()
    def _add_layer(self) -> None:
        n   = len(self._config.layers) + 1
        mat = self._materials[0] if self._materials else "air"
        self._config.layers.append(
            LayerSpec(name=f"Layer {n}", material=mat, thickness_nm=100.0)
        )
        self._rebuild_rows()
        self.changed.emit()

    @Slot()
    def _add_mixed(self) -> None:
        dlg = MixedLayerDialog(self._materials, parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.result:
            self._config.layers.append(dlg.result)
            self._rebuild_rows()
            self.changed.emit()

    @Slot(int)
    def _delete_layer(self, index: int) -> None:
        if 0 <= index < len(self._config.layers):
            del self._config.layers[index]
            self._rebuild_rows()
            self.changed.emit()

    @Slot(int, int)
    def _move_layer(self, index: int, delta: int) -> None:
        layers  = self._config.layers
        new_idx = index + delta
        if 0 <= new_idx < len(layers):
            layers[index], layers[new_idx] = layers[new_idx], layers[index]
            self._rebuild_rows()
            self.changed.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_config(self) -> StackConfig:
        return self._config

    def set_config(self, config: StackConfig) -> None:
        self._config = config
        self.ui.combo_superstrate.blockSignals(True)
        self.ui.combo_substrate.blockSignals(True)
        self.ui.combo_superstrate.setCurrentText(config.superstrate)
        self.ui.combo_substrate.setCurrentText(config.substrate)
        self.ui.combo_superstrate.blockSignals(False)
        self.ui.combo_substrate.blockSignals(False)
        self._rebuild_rows()

    def update_materials(self, materials: list[str]) -> None:
        self._materials = materials
        for row in self._rows:
            row.update_materials(materials)
