import os
from PyQt5 import QtGui, uic
from qgis.gui import (QgsOptionsPageWidget)
from qgis.PyQt.QtWidgets import  QVBoxLayout
from .qgissettingmanager import *
import logging


WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), 'settings.ui')
)

class ConfigOptionsPage(QgsOptionsPageWidget):

    def __init__(self, parent, settings):
        super(ConfigOptionsPage, self).__init__(parent)
        self.settings = settings
        self.config_widget = ConfigDialog(self.settings)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setMargin(0)
        self.setLayout(layout)
        layout.addWidget(self.config_widget)
        self.setObjectName('DmiOpenDataOptions')

    def apply(self):
        self.config_widget.accept_dialog()
        self.settings.emit_updated()


class ConfigDialog(WIDGET, BASE, SettingDialog):
    def __init__(self, settings):
        super(ConfigDialog, self).__init__(setting_manager=settings)
        self.setupUi(self)
        self.settings = settings
        self.init_widgets()

