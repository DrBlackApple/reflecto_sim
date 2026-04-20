# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mixed_layer_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QSizePolicy, QSlider, QVBoxLayout,
    QWidget)

class Ui_MixedLayerDialog(object):
    def setupUi(self, MixedLayerDialog):
        if not MixedLayerDialog.objectName():
            MixedLayerDialog.setObjectName(u"MixedLayerDialog")
        MixedLayerDialog.resize(340, 280)
        MixedLayerDialog.setSizeGripEnabled(False)
        self.vl_main = QVBoxLayout(MixedLayerDialog)
        self.vl_main.setObjectName(u"vl_main")
        self.vl_main.setContentsMargins(12, 12, 12, 12)
        self.fl_fields = QFormLayout()
        self.fl_fields.setObjectName(u"fl_fields")
        self.fl_fields.setRowWrapPolicy(QFormLayout.DontWrapRows)
        self.lbl_name = QLabel(MixedLayerDialog)
        self.lbl_name.setObjectName(u"lbl_name")

        self.fl_fields.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_name)

        self.edit_name = QLineEdit(MixedLayerDialog)
        self.edit_name.setObjectName(u"edit_name")

        self.fl_fields.setWidget(0, QFormLayout.ItemRole.FieldRole, self.edit_name)

        self.lbl_mat_a = QLabel(MixedLayerDialog)
        self.lbl_mat_a.setObjectName(u"lbl_mat_a")

        self.fl_fields.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lbl_mat_a)

        self.combo_mat_a = QComboBox(MixedLayerDialog)
        self.combo_mat_a.setObjectName(u"combo_mat_a")
        self.combo_mat_a.setEditable(False)

        self.fl_fields.setWidget(1, QFormLayout.ItemRole.FieldRole, self.combo_mat_a)

        self.lbl_mat_b = QLabel(MixedLayerDialog)
        self.lbl_mat_b.setObjectName(u"lbl_mat_b")

        self.fl_fields.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lbl_mat_b)

        self.combo_mat_b = QComboBox(MixedLayerDialog)
        self.combo_mat_b.setObjectName(u"combo_mat_b")
        self.combo_mat_b.setEditable(False)

        self.fl_fields.setWidget(2, QFormLayout.ItemRole.FieldRole, self.combo_mat_b)

        self.lbl_fraction = QLabel(MixedLayerDialog)
        self.lbl_fraction.setObjectName(u"lbl_fraction")

        self.fl_fields.setWidget(3, QFormLayout.ItemRole.LabelRole, self.lbl_fraction)

        self.hl_fraction = QHBoxLayout()
        self.hl_fraction.setObjectName(u"hl_fraction")
        self.slider_fraction = QSlider(MixedLayerDialog)
        self.slider_fraction.setObjectName(u"slider_fraction")
        self.slider_fraction.setMinimum(0)
        self.slider_fraction.setMaximum(100)
        self.slider_fraction.setValue(50)
        self.slider_fraction.setOrientation(Qt.Horizontal)

        self.hl_fraction.addWidget(self.slider_fraction)

        self.lbl_fraction_val = QLabel(MixedLayerDialog)
        self.lbl_fraction_val.setObjectName(u"lbl_fraction_val")
        self.lbl_fraction_val.setMinimumWidth(36)
        self.lbl_fraction_val.setAlignment(Qt.AlignRight|Qt.AlignVCenter)

        self.hl_fraction.addWidget(self.lbl_fraction_val)


        self.fl_fields.setLayout(3, QFormLayout.ItemRole.FieldRole, self.hl_fraction)

        self.lbl_thickness = QLabel(MixedLayerDialog)
        self.lbl_thickness.setObjectName(u"lbl_thickness")

        self.fl_fields.setWidget(4, QFormLayout.ItemRole.LabelRole, self.lbl_thickness)

        self.edit_thickness = QLineEdit(MixedLayerDialog)
        self.edit_thickness.setObjectName(u"edit_thickness")

        self.fl_fields.setWidget(4, QFormLayout.ItemRole.FieldRole, self.edit_thickness)

        self.lbl_model = QLabel(MixedLayerDialog)
        self.lbl_model.setObjectName(u"lbl_model")

        self.fl_fields.setWidget(5, QFormLayout.ItemRole.LabelRole, self.lbl_model)

        self.combo_model = QComboBox(MixedLayerDialog)
        self.combo_model.setObjectName(u"combo_model")
        self.combo_model.setEditable(False)

        self.fl_fields.setWidget(5, QFormLayout.ItemRole.FieldRole, self.combo_model)


        self.vl_main.addLayout(self.fl_fields)

        self.button_box = QDialogButtonBox(MixedLayerDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)

        self.vl_main.addWidget(self.button_box)


        self.retranslateUi(MixedLayerDialog)
        self.button_box.accepted.connect(MixedLayerDialog.accept)
        self.button_box.rejected.connect(MixedLayerDialog.reject)

        QMetaObject.connectSlotsByName(MixedLayerDialog)
    # setupUi

    def retranslateUi(self, MixedLayerDialog):
        MixedLayerDialog.setWindowTitle(QCoreApplication.translate("MixedLayerDialog", u"Mixed layer", None))
        self.lbl_name.setText(QCoreApplication.translate("MixedLayerDialog", u"Name:", None))
        self.lbl_mat_a.setText(QCoreApplication.translate("MixedLayerDialog", u"Material A (f):", None))
        self.lbl_mat_b.setText(QCoreApplication.translate("MixedLayerDialog", u"Material B (1-f):", None))
        self.lbl_fraction.setText(QCoreApplication.translate("MixedLayerDialog", u"Volume fraction f:", None))
        self.lbl_fraction_val.setText(QCoreApplication.translate("MixedLayerDialog", u"0.50", None))
        self.lbl_thickness.setText(QCoreApplication.translate("MixedLayerDialog", u"Thickness (nm):", None))
        self.edit_thickness.setText(QCoreApplication.translate("MixedLayerDialog", u"100", None))
        self.lbl_model.setText(QCoreApplication.translate("MixedLayerDialog", u"Model:", None))
    # retranslateUi

