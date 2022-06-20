import os
from pathlib import Path
from qgis.gui import (QgsOptionsWidgetFactory)
from qgis.core import QgsApplication
from PyQt5.QtGui import QIcon
from .settings_dialog import ConfigOptionsPage


class OptionsFactory(QgsOptionsWidgetFactory):
    def __init__(self, settings):
        super(QgsOptionsWidgetFactory, self).__init__()
        self.settings = settings

    def icon(self):
        icon_path = os.path.join(str(Path(os.path.dirname(__file__)).parent.absolute()), 'icon.png')
        return QIcon (icon_path)

    def createWidget(self, parent):
        return ConfigOptionsPage(parent, self.settings)
