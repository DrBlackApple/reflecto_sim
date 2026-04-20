# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plot_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QSizePolicy, QVBoxLayout,
    QWidget)

from pyqtgraph import GraphicsLayoutWidget

class Ui_PlotPanel(object):
    def setupUi(self, PlotPanel):
        if not PlotPanel.objectName():
            PlotPanel.setObjectName(u"PlotPanel")
        PlotPanel.resize(800, 600)
        self.vl_main = QVBoxLayout(PlotPanel)
        self.vl_main.setObjectName(u"vl_main")
        self.vl_main.setContentsMargins(0, 0, 0, 0)
        self.glw = GraphicsLayoutWidget(PlotPanel)
        self.glw.setObjectName(u"glw")

        self.vl_main.addWidget(self.glw)

        self.lbl_hover = QLabel(PlotPanel)
        self.lbl_hover.setObjectName(u"lbl_hover")
        self.lbl_hover.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.lbl_hover.setMaximumHeight(20)

        self.vl_main.addWidget(self.lbl_hover)


        self.retranslateUi(PlotPanel)

        QMetaObject.connectSlotsByName(PlotPanel)
    # setupUi

    def retranslateUi(self, PlotPanel):
        self.lbl_hover.setText("")
        pass
    # retranslateUi

