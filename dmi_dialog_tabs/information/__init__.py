# -*- coding: utf-8 -*-
import os
import webbrowser
from qgis.PyQt import QtWidgets, uic

from ...settings import DMISettingsManager

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'information.ui'))

print(os.path.join(os.path.dirname(__file__), 'information.ui'))

class DMIInformationWidget(QtWidgets.QWidget, FORM_CLASS):
    def __init__(self, settings_manager: DMISettingsManager, parent=None):
        super(DMIInformationWidget, self).__init__(parent)
        super(DMIInformationWidget, self).setupUi(self)

        self.dmi_open_data.clicked.connect(self.open_openData)
        self.dmi_dk.clicked.connect(self.open_dmi_dk)

    # Actions for buttons to go to dmi.dk
    def open_openData(self):
        webbrowser.open('https://confluence.govcloud.dk/display/FDAPI/Danish+Meteorological+Institute+-+Open+Data')
    def open_dmi_dk(self):
        webbrowser.open('https://www.dmi.dk/')
