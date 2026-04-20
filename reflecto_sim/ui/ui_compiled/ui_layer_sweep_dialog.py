# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layer_sweep_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QStackedWidget, QVBoxLayout, QWidget)

class Ui_LayerSweepDialog(object):
    def setupUi(self, LayerSweepDialog):
        if not LayerSweepDialog.objectName():
            LayerSweepDialog.setObjectName(u"LayerSweepDialog")
        LayerSweepDialog.resize(340, 320)
        self.vl_main = QVBoxLayout(LayerSweepDialog)
        self.vl_main.setObjectName(u"vl_main")
        self.vl_main.setContentsMargins(12, 12, 12, 12)
        self.hl_mode = QHBoxLayout()
        self.hl_mode.setObjectName(u"hl_mode")
        self.lbl_mode = QLabel(LayerSweepDialog)
        self.lbl_mode.setObjectName(u"lbl_mode")

        self.hl_mode.addWidget(self.lbl_mode)

        self.radio_none = QRadioButton(LayerSweepDialog)
        self.radio_none.setObjectName(u"radio_none")
        self.radio_none.setChecked(True)

        self.hl_mode.addWidget(self.radio_none)

        self.radio_material = QRadioButton(LayerSweepDialog)
        self.radio_material.setObjectName(u"radio_material")

        self.hl_mode.addWidget(self.radio_material)

        self.radio_mix = QRadioButton(LayerSweepDialog)
        self.radio_mix.setObjectName(u"radio_mix")

        self.hl_mode.addWidget(self.radio_mix)

        self.spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_mode.addItem(self.spacerItem)


        self.vl_main.addLayout(self.hl_mode)

        self.content_stack = QStackedWidget(LayerSweepDialog)
        self.content_stack.setObjectName(u"content_stack")
        self.page_none = QWidget()
        self.page_none.setObjectName(u"page_none")
        self.vl_none = QVBoxLayout(self.page_none)
        self.vl_none.setObjectName(u"vl_none")
        self.lbl_none_info = QLabel(self.page_none)
        self.lbl_none_info.setObjectName(u"lbl_none_info")
        self.lbl_none_info.setAlignment(Qt.AlignCenter)

        self.vl_none.addWidget(self.lbl_none_info)

        self.content_stack.addWidget(self.page_none)
        self.page_material = QWidget()
        self.page_material.setObjectName(u"page_material")
        self.vl_material = QVBoxLayout(self.page_material)
        self.vl_material.setObjectName(u"vl_material")
        self.lbl_mat_hint = QLabel(self.page_material)
        self.lbl_mat_hint.setObjectName(u"lbl_mat_hint")

        self.vl_material.addWidget(self.lbl_mat_hint)

        self.list_materials = QListWidget(self.page_material)
        self.list_materials.setObjectName(u"list_materials")
        self.list_materials.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.vl_material.addWidget(self.list_materials)

        self.hl_mat_btns = QHBoxLayout()
        self.hl_mat_btns.setObjectName(u"hl_mat_btns")
        self.btn_select_all = QPushButton(self.page_material)
        self.btn_select_all.setObjectName(u"btn_select_all")

        self.hl_mat_btns.addWidget(self.btn_select_all)

        self.btn_clear_sel = QPushButton(self.page_material)
        self.btn_clear_sel.setObjectName(u"btn_clear_sel")

        self.hl_mat_btns.addWidget(self.btn_clear_sel)

        self.spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_mat_btns.addItem(self.spacerItem1)


        self.vl_material.addLayout(self.hl_mat_btns)

        self.content_stack.addWidget(self.page_material)
        self.page_mix = QWidget()
        self.page_mix.setObjectName(u"page_mix")
        self.vl_mix = QVBoxLayout(self.page_mix)
        self.vl_mix.setObjectName(u"vl_mix")
        self.fl_mix = QFormLayout()
        self.fl_mix.setObjectName(u"fl_mix")
        self.lbl_mix_mat_b = QLabel(self.page_mix)
        self.lbl_mix_mat_b.setObjectName(u"lbl_mix_mat_b")

        self.fl_mix.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_mix_mat_b)

        self.combo_mix_mat_b = QComboBox(self.page_mix)
        self.combo_mix_mat_b.setObjectName(u"combo_mix_mat_b")
        self.combo_mix_mat_b.setEditable(False)

        self.fl_mix.setWidget(0, QFormLayout.ItemRole.FieldRole, self.combo_mix_mat_b)

        self.lbl_mix_model = QLabel(self.page_mix)
        self.lbl_mix_model.setObjectName(u"lbl_mix_model")

        self.fl_mix.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lbl_mix_model)

        self.combo_mix_model = QComboBox(self.page_mix)
        self.combo_mix_model.setObjectName(u"combo_mix_model")
        self.combo_mix_model.setEditable(False)

        self.fl_mix.setWidget(1, QFormLayout.ItemRole.FieldRole, self.combo_mix_model)

        self.lbl_n_pts = QLabel(self.page_mix)
        self.lbl_n_pts.setObjectName(u"lbl_n_pts")

        self.fl_mix.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lbl_n_pts)

        self.spin_n_pts = QSpinBox(self.page_mix)
        self.spin_n_pts.setObjectName(u"spin_n_pts")
        self.spin_n_pts.setMinimum(2)
        self.spin_n_pts.setMaximum(200)
        self.spin_n_pts.setValue(20)

        self.fl_mix.setWidget(2, QFormLayout.ItemRole.FieldRole, self.spin_n_pts)


        self.vl_mix.addLayout(self.fl_mix)

        self.lbl_mix_hint = QLabel(self.page_mix)
        self.lbl_mix_hint.setObjectName(u"lbl_mix_hint")

        self.vl_mix.addWidget(self.lbl_mix_hint)

        self.spacerItem2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vl_mix.addItem(self.spacerItem2)

        self.content_stack.addWidget(self.page_mix)

        self.vl_main.addWidget(self.content_stack)

        self.button_box = QDialogButtonBox(LayerSweepDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)

        self.vl_main.addWidget(self.button_box)


        self.retranslateUi(LayerSweepDialog)
        self.button_box.accepted.connect(LayerSweepDialog.accept)
        self.button_box.rejected.connect(LayerSweepDialog.reject)

        QMetaObject.connectSlotsByName(LayerSweepDialog)
    # setupUi

    def retranslateUi(self, LayerSweepDialog):
        LayerSweepDialog.setWindowTitle(QCoreApplication.translate("LayerSweepDialog", u"Sweep config", None))
        self.lbl_mode.setText(QCoreApplication.translate("LayerSweepDialog", u"Mode:", None))
        self.radio_none.setText(QCoreApplication.translate("LayerSweepDialog", u"None", None))
        self.radio_material.setText(QCoreApplication.translate("LayerSweepDialog", u"Material", None))
        self.radio_mix.setText(QCoreApplication.translate("LayerSweepDialog", u"Mix fraction", None))
        self.lbl_none_info.setText(QCoreApplication.translate("LayerSweepDialog", u"No sweep \u2014 single spectrum.", None))
        self.lbl_mat_hint.setText(QCoreApplication.translate("LayerSweepDialog", u"Materials to sweep:", None))
        self.btn_select_all.setText(QCoreApplication.translate("LayerSweepDialog", u"Select All", None))
        self.btn_clear_sel.setText(QCoreApplication.translate("LayerSweepDialog", u"Clear", None))
        self.lbl_mix_mat_b.setText(QCoreApplication.translate("LayerSweepDialog", u"Material B (f=0):", None))
        self.lbl_mix_model.setText(QCoreApplication.translate("LayerSweepDialog", u"Model:", None))
        self.lbl_n_pts.setText(QCoreApplication.translate("LayerSweepDialog", u"N points:", None))
        self.lbl_mix_hint.setText(QCoreApplication.translate("LayerSweepDialog", u"(Mat A = current, f=1)", None))
    # retranslateUi

