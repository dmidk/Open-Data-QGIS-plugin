from PyQt5.QtCore import QObject

from .qgissettingmanager import *
from qgis.PyQt import QtCore
from enum import Enum


class DMISettingKeys(Enum):
    """
    Holds the keys for this plugin settings retrievable by the DMISettingsManager. Note that these should match the
    object names of the settings input widgets in settings.ui file.
    """
    METOBS_API_KEY = 'DMI_apiKey_metObs'
    OCEANOBS_API_KEY = 'DMI_apiKey_oceanObs'
    CLIMATEDATA_API_KEY = 'DMI_apiKey_climateData'
    LIGHTNINGDATA_API_KEY = 'DMI_apiKey_lightningData'
    RADARDATA_API_KEY = 'DMI_apiKey_radarData'
    FORECASTDATA_API_KEY = 'DMI_apiKey_forecastData'

    def get_api_name(self) -> str:
        if self is DMISettingKeys.METOBS_API_KEY:
            return 'MetObs'
        if self is DMISettingKeys.OCEANOBS_API_KEY:
            return 'OceanObs'
        if self is DMISettingKeys.CLIMATEDATA_API_KEY:
            return 'Climate Data'
        if self is DMISettingKeys.LIGHTNINGDATA_API_KEY:
            return 'Lightning Data'
        if self is DMISettingKeys.RADARDATA_API_KEY:
            return 'Radar Data'
        if self is DMISettingKeys.RADARDATA_API_KEY:
            return 'Forecast Data'


class DMISettingsManager(SettingManager, QObject):
    settings_updated = QtCore.pyqtSignal()

    def __init__(self):
        SettingManager.__init__(self, 'DMI Open Data')
        QObject.__init__(self)
        self.add_setting(String(DMISettingKeys.METOBS_API_KEY.value, Scope.Global, ''))
        self.add_setting(String(DMISettingKeys.OCEANOBS_API_KEY.value, Scope.Global, ''))
        self.add_setting(String(DMISettingKeys.CLIMATEDATA_API_KEY.value, Scope.Global, ''))
        self.add_setting(String(DMISettingKeys.LIGHTNINGDATA_API_KEY.value, Scope.Global, ''))
        self.add_setting(String(DMISettingKeys.RADARDATA_API_KEY.value, Scope.Global, ''))
        self.add_setting(String(DMISettingKeys.FORECASTDATA_API_KEY.value, Scope.Global, ''))

    def emit_updated(self):
        self.settings_updated.emit()
