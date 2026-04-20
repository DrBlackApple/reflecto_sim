# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMenu, QMenuBar, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1400, 800)
        self.action_open = QAction(MainWindow)
        self.action_open.setObjectName(u"action_open")
        self.action_save = QAction(MainWindow)
        self.action_save.setObjectName(u"action_save")
        self.action_exit = QAction(MainWindow)
        self.action_exit.setObjectName(u"action_exit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.hl_main = QHBoxLayout(self.centralwidget)
        self.hl_main.setSpacing(4)
        self.hl_main.setObjectName(u"hl_main")
        self.hl_main.setContentsMargins(4, 4, 4, 4)
        self.left_container = QWidget(self.centralwidget)
        self.left_container.setObjectName(u"left_container")
        self.left_container.setMinimumWidth(420)
        self.left_container.setMaximumWidth(460)
        self.vl_left = QVBoxLayout(self.left_container)
        self.vl_left.setObjectName(u"vl_left")
        self.vl_left.setContentsMargins(0, 0, 0, 0)
        self.lbl_stack_title = QLabel(self.left_container)
        self.lbl_stack_title.setObjectName(u"lbl_stack_title")

        self.vl_left.addWidget(self.lbl_stack_title)


        self.hl_main.addWidget(self.left_container)

        self.centre_container = QWidget(self.centralwidget)
        self.centre_container.setObjectName(u"centre_container")
        self.vl_centre = QVBoxLayout(self.centre_container)
        self.vl_centre.setObjectName(u"vl_centre")
        self.vl_centre.setContentsMargins(0, 0, 0, 0)

        self.hl_main.addWidget(self.centre_container)

        self.right_panel = QWidget(self.centralwidget)
        self.right_panel.setObjectName(u"right_panel")
        self.right_panel.setMinimumWidth(200)
        self.right_panel.setMaximumWidth(240)
        self.vl_right = QVBoxLayout(self.right_panel)
        self.vl_right.setSpacing(4)
        self.vl_right.setObjectName(u"vl_right")
        self.vl_right.setContentsMargins(6, 6, 6, 6)
        self.lbl_sim_title = QLabel(self.right_panel)
        self.lbl_sim_title.setObjectName(u"lbl_sim_title")

        self.vl_right.addWidget(self.lbl_sim_title)

        self.sep1 = QFrame(self.right_panel)
        self.sep1.setObjectName(u"sep1")
        self.sep1.setFrameShape(QFrame.HLine)
        self.sep1.setFrameShadow(QFrame.Plain)

        self.vl_right.addWidget(self.sep1)

        self.fl_wavelength = QFormLayout()
        self.fl_wavelength.setObjectName(u"fl_wavelength")
        self.lbl_lam_min = QLabel(self.right_panel)
        self.lbl_lam_min.setObjectName(u"lbl_lam_min")

        self.fl_wavelength.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_lam_min)

        self.edit_lam_min = QLineEdit(self.right_panel)
        self.edit_lam_min.setObjectName(u"edit_lam_min")

        self.fl_wavelength.setWidget(0, QFormLayout.ItemRole.FieldRole, self.edit_lam_min)

        self.lbl_lam_max = QLabel(self.right_panel)
        self.lbl_lam_max.setObjectName(u"lbl_lam_max")

        self.fl_wavelength.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lbl_lam_max)

        self.edit_lam_max = QLineEdit(self.right_panel)
        self.edit_lam_max.setObjectName(u"edit_lam_max")

        self.fl_wavelength.setWidget(1, QFormLayout.ItemRole.FieldRole, self.edit_lam_max)

        self.lbl_lam_step = QLabel(self.right_panel)
        self.lbl_lam_step.setObjectName(u"lbl_lam_step")

        self.fl_wavelength.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lbl_lam_step)

        self.edit_lam_step = QLineEdit(self.right_panel)
        self.edit_lam_step.setObjectName(u"edit_lam_step")

        self.fl_wavelength.setWidget(2, QFormLayout.ItemRole.FieldRole, self.edit_lam_step)


        self.vl_right.addLayout(self.fl_wavelength)

        self.sep2 = QFrame(self.right_panel)
        self.sep2.setObjectName(u"sep2")
        self.sep2.setFrameShape(QFrame.HLine)
        self.sep2.setFrameShadow(QFrame.Plain)

        self.vl_right.addWidget(self.sep2)

        self.fl_angle = QFormLayout()
        self.fl_angle.setObjectName(u"fl_angle")
        self.lbl_angle = QLabel(self.right_panel)
        self.lbl_angle.setObjectName(u"lbl_angle")

        self.fl_angle.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_angle)

        self.edit_angle = QLineEdit(self.right_panel)
        self.edit_angle.setObjectName(u"edit_angle")

        self.fl_angle.setWidget(0, QFormLayout.ItemRole.FieldRole, self.edit_angle)


        self.vl_right.addLayout(self.fl_angle)

        self.hl_pol = QHBoxLayout()
        self.hl_pol.setObjectName(u"hl_pol")
        self.lbl_pol = QLabel(self.right_panel)
        self.lbl_pol.setObjectName(u"lbl_pol")

        self.hl_pol.addWidget(self.lbl_pol)

        self.radio_pol_s = QRadioButton(self.right_panel)
        self.radio_pol_s.setObjectName(u"radio_pol_s")
        self.radio_pol_s.setChecked(True)

        self.hl_pol.addWidget(self.radio_pol_s)

        self.radio_pol_p = QRadioButton(self.right_panel)
        self.radio_pol_p.setObjectName(u"radio_pol_p")

        self.hl_pol.addWidget(self.radio_pol_p)

        self.radio_pol_both = QRadioButton(self.right_panel)
        self.radio_pol_both.setObjectName(u"radio_pol_both")
        self.radio_pol_both.setVisible(False)

        self.hl_pol.addWidget(self.radio_pol_both)

        self.spacerItem = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hl_pol.addItem(self.spacerItem)


        self.vl_right.addLayout(self.hl_pol)

        self.sep3 = QFrame(self.right_panel)
        self.sep3.setObjectName(u"sep3")
        self.sep3.setFrameShape(QFrame.HLine)
        self.sep3.setFrameShadow(QFrame.Plain)

        self.vl_right.addWidget(self.sep3)

        self.chk_unwrap = QCheckBox(self.right_panel)
        self.chk_unwrap.setObjectName(u"chk_unwrap")

        self.vl_right.addWidget(self.chk_unwrap)

        self.chk_autofit = QCheckBox(self.right_panel)
        self.chk_autofit.setObjectName(u"chk_autofit")

        self.vl_right.addWidget(self.chk_autofit)

        self.chk_log_y = QCheckBox(self.right_panel)
        self.chk_log_y.setObjectName(u"chk_log_y")

        self.vl_right.addWidget(self.chk_log_y)

        self.sep4 = QFrame(self.right_panel)
        self.sep4.setObjectName(u"sep4")
        self.sep4.setFrameShape(QFrame.HLine)
        self.sep4.setFrameShadow(QFrame.Plain)

        self.vl_right.addWidget(self.sep4)

        self.lbl_obj_title = QLabel(self.right_panel)
        self.lbl_obj_title.setObjectName(u"lbl_obj_title")

        self.vl_right.addWidget(self.lbl_obj_title)

        self.fl_na = QFormLayout()
        self.fl_na.setObjectName(u"fl_na")
        self.lbl_na = QLabel(self.right_panel)
        self.lbl_na.setObjectName(u"lbl_na")

        self.fl_na.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_na)

        self.edit_na = QLineEdit(self.right_panel)
        self.edit_na.setObjectName(u"edit_na")

        self.fl_na.setWidget(0, QFormLayout.ItemRole.FieldRole, self.edit_na)

        self.lbl_magnif = QLabel(self.right_panel)
        self.lbl_magnif.setObjectName(u"lbl_magnif")

        self.fl_na.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lbl_magnif)

        self.edit_magnif = QLineEdit(self.right_panel)
        self.edit_magnif.setObjectName(u"edit_magnif")

        self.fl_na.setWidget(1, QFormLayout.ItemRole.FieldRole, self.edit_magnif)


        self.vl_right.addLayout(self.fl_na)

        self.chk_use_na = QCheckBox(self.right_panel)
        self.chk_use_na.setObjectName(u"chk_use_na")

        self.vl_right.addWidget(self.chk_use_na)

        self.sep5 = QFrame(self.right_panel)
        self.sep5.setObjectName(u"sep5")
        self.sep5.setFrameShape(QFrame.HLine)
        self.sep5.setFrameShadow(QFrame.Plain)

        self.vl_right.addWidget(self.sep5)

        self.btn_compute = QPushButton(self.right_panel)
        self.btn_compute.setObjectName(u"btn_compute")

        self.vl_right.addWidget(self.btn_compute)

        self.btn_clear_plot = QPushButton(self.right_panel)
        self.btn_clear_plot.setObjectName(u"btn_clear_plot")

        self.vl_right.addWidget(self.btn_clear_plot)

        self.sep6 = QFrame(self.right_panel)
        self.sep6.setObjectName(u"sep6")
        self.sep6.setFrameShape(QFrame.HLine)
        self.sep6.setFrameShadow(QFrame.Plain)

        self.vl_right.addWidget(self.sep6)

        self.lbl_export = QLabel(self.right_panel)
        self.lbl_export.setObjectName(u"lbl_export")

        self.vl_right.addWidget(self.lbl_export)

        self.btn_save_csv = QPushButton(self.right_panel)
        self.btn_save_csv.setObjectName(u"btn_save_csv")

        self.vl_right.addWidget(self.btn_save_csv)

        self.btn_save_png = QPushButton(self.right_panel)
        self.btn_save_png.setObjectName(u"btn_save_png")

        self.vl_right.addWidget(self.btn_save_png)

        self.spacerItem1 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vl_right.addItem(self.spacerItem1)

        self.lbl_status = QLabel(self.right_panel)
        self.lbl_status.setObjectName(u"lbl_status")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setAlignment(Qt.AlignLeft|Qt.AlignTop)

        self.vl_right.addWidget(self.lbl_status)


        self.hl_main.addWidget(self.right_panel)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1400, 22))
        self.menu_file = QMenu(self.menubar)
        self.menu_file.setObjectName(u"menu_file")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menu_file.addAction(self.action_open)
        self.menu_file.addAction(self.action_save)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"reflecto_sim \u2014 Reflectometry Simulator", None))
        self.action_open.setText(QCoreApplication.translate("MainWindow", u"Open stack\u2026", None))
#if QT_CONFIG(shortcut)
        self.action_open.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.action_save.setText(QCoreApplication.translate("MainWindow", u"Save stack\u2026", None))
#if QT_CONFIG(shortcut)
        self.action_save.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.action_exit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.lbl_stack_title.setText(QCoreApplication.translate("MainWindow", u"Stack Editor", None))
        self.lbl_sim_title.setText(QCoreApplication.translate("MainWindow", u"Simulation", None))
        self.lbl_lam_min.setText(QCoreApplication.translate("MainWindow", u"\u03bb min (nm):", None))
        self.edit_lam_min.setText(QCoreApplication.translate("MainWindow", u"430", None))
        self.lbl_lam_max.setText(QCoreApplication.translate("MainWindow", u"\u03bb max (nm):", None))
        self.edit_lam_max.setText(QCoreApplication.translate("MainWindow", u"1600", None))
        self.lbl_lam_step.setText(QCoreApplication.translate("MainWindow", u"Step (nm):", None))
        self.edit_lam_step.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.lbl_angle.setText(QCoreApplication.translate("MainWindow", u"Angle (\u00b0):", None))
        self.edit_angle.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.lbl_pol.setText(QCoreApplication.translate("MainWindow", u"Pol.:", None))
        self.radio_pol_s.setText(QCoreApplication.translate("MainWindow", u"s", None))
        self.radio_pol_p.setText(QCoreApplication.translate("MainWindow", u"p", None))
        self.radio_pol_both.setText(QCoreApplication.translate("MainWindow", u"both", None))
        self.chk_unwrap.setText(QCoreApplication.translate("MainWindow", u"Unwrap phase", None))
        self.chk_autofit.setText(QCoreApplication.translate("MainWindow", u"Autofit Y", None))
        self.chk_log_y.setText(QCoreApplication.translate("MainWindow", u"Log Y", None))
        self.lbl_obj_title.setText(QCoreApplication.translate("MainWindow", u"Objective", None))
        self.lbl_na.setText(QCoreApplication.translate("MainWindow", u"NA:", None))
        self.edit_na.setText(QCoreApplication.translate("MainWindow", u"0.0", None))
        self.lbl_magnif.setText(QCoreApplication.translate("MainWindow", u"Magnif. (\u00d7):", None))
        self.edit_magnif.setText(QCoreApplication.translate("MainWindow", u"10", None))
        self.chk_use_na.setText(QCoreApplication.translate("MainWindow", u"Use NA integration", None))
        self.btn_compute.setText(QCoreApplication.translate("MainWindow", u"\u25b6  Compute", None))
        self.btn_clear_plot.setText(QCoreApplication.translate("MainWindow", u"Clear plot", None))
        self.lbl_export.setText(QCoreApplication.translate("MainWindow", u"Export:", None))
        self.btn_save_csv.setText(QCoreApplication.translate("MainWindow", u"Save CSV", None))
        self.btn_save_png.setText(QCoreApplication.translate("MainWindow", u"Save PNG", None))
        self.lbl_status.setText(QCoreApplication.translate("MainWindow", u"Ready", None))
        self.menu_file.setTitle(QCoreApplication.translate("MainWindow", u"&File", None))
    # retranslateUi

