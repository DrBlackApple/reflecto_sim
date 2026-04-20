# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'stack_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_StackEditor(object):
    def setupUi(self, StackEditor):
        if not StackEditor.objectName():
            StackEditor.setObjectName(u"StackEditor")
        StackEditor.resize(300, 600)
        self.vl_main = QVBoxLayout(StackEditor)
        self.vl_main.setObjectName(u"vl_main")
        self.vl_main.setContentsMargins(6, 6, 6, 6)
        self.hl_superstrate = QHBoxLayout()
        self.hl_superstrate.setObjectName(u"hl_superstrate")
        self.lbl_superstrate = QLabel(StackEditor)
        self.lbl_superstrate.setObjectName(u"lbl_superstrate")

        self.hl_superstrate.addWidget(self.lbl_superstrate)

        self.combo_superstrate = QComboBox(StackEditor)
        self.combo_superstrate.setObjectName(u"combo_superstrate")
        self.combo_superstrate.setEditable(False)
        self.combo_superstrate.setMinimumWidth(120)

        self.hl_superstrate.addWidget(self.combo_superstrate)

        self.spacerItem = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_superstrate.addItem(self.spacerItem)


        self.vl_main.addLayout(self.hl_superstrate)

        self.lbl_layers = QLabel(StackEditor)
        self.lbl_layers.setObjectName(u"lbl_layers")

        self.vl_main.addWidget(self.lbl_layers)

        self.scroll_area = QScrollArea(StackEditor)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.layers_container = QWidget()
        self.layers_container.setObjectName(u"layers_container")
        self.layers_container.setGeometry(QRect(0, 0, 420, 400))
        self.vl_layers = QVBoxLayout(self.layers_container)
        self.vl_layers.setObjectName(u"vl_layers")
        self.vl_layers.setContentsMargins(2, 2, 2, 2)
        self.spacerItem1 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vl_layers.addItem(self.spacerItem1)

        self.scroll_area.setWidget(self.layers_container)

        self.vl_main.addWidget(self.scroll_area)

        self.hl_buttons = QHBoxLayout()
        self.hl_buttons.setObjectName(u"hl_buttons")
        self.btn_add_layer = QPushButton(StackEditor)
        self.btn_add_layer.setObjectName(u"btn_add_layer")

        self.hl_buttons.addWidget(self.btn_add_layer)

        self.btn_add_mixed = QPushButton(StackEditor)
        self.btn_add_mixed.setObjectName(u"btn_add_mixed")

        self.hl_buttons.addWidget(self.btn_add_mixed)

        self.spacerItem2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_buttons.addItem(self.spacerItem2)


        self.vl_main.addLayout(self.hl_buttons)

        self.hl_substrate = QHBoxLayout()
        self.hl_substrate.setObjectName(u"hl_substrate")
        self.lbl_substrate = QLabel(StackEditor)
        self.lbl_substrate.setObjectName(u"lbl_substrate")

        self.hl_substrate.addWidget(self.lbl_substrate)

        self.combo_substrate = QComboBox(StackEditor)
        self.combo_substrate.setObjectName(u"combo_substrate")
        self.combo_substrate.setEditable(False)
        self.combo_substrate.setMinimumWidth(120)

        self.hl_substrate.addWidget(self.combo_substrate)

        self.spacerItem3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_substrate.addItem(self.spacerItem3)


        self.vl_main.addLayout(self.hl_substrate)


        self.retranslateUi(StackEditor)

        QMetaObject.connectSlotsByName(StackEditor)
    # setupUi

    def retranslateUi(self, StackEditor):
        self.lbl_superstrate.setText(QCoreApplication.translate("StackEditor", u"Superstrate:", None))
        self.lbl_layers.setText(QCoreApplication.translate("StackEditor", u"Layers (top \u2192 bottom):", None))
        self.btn_add_layer.setText(QCoreApplication.translate("StackEditor", u"+ Layer", None))
        self.btn_add_mixed.setText(QCoreApplication.translate("StackEditor", u"+ Mixed", None))
        self.lbl_substrate.setText(QCoreApplication.translate("StackEditor", u"Substrate:", None))
        pass
    # retranslateUi

