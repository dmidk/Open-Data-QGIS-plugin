# -*- coding: utf-8 -*-
import os
from typing import Tuple, Dict, Set
from qgis.PyQt import QtWidgets, uic
import requests
import pandas as pd
from pandas import json_normalize
import warnings
from tempfile import mkdtemp
from qgis.core import QgsVectorLayer, QgsProcessing, QgsProcessingFeedback, QgsRasterLayer, QgsContrastEnhancement, QgsRasterMinMaxOrigin, QgsFeature, QgsGeometry, QgsField, QgsPointXY, QgsProject, QgsRasterLayerTemporalProperties, QgsDateTimeRange, QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsSingleBandGrayRenderer, QgsRasterBandStats
from qgis.PyQt.QtGui import (
    QColor)
from qgis.utils import iface
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from qgis.PyQt.QtCore import QVariant
import webbrowser
from .forecast_para import depth_para_dkss, salinity_nsbs, salinity_idw, salinity_if, salinity_lb, salinity_lf, salinity_ws, water_temp_nsbs, water_temp_if, water_temp_lb, water_temp_lf, water_temp_ws, water_temp_idw, v_current_nsbs, v_current_idw, v_current_if, v_current_lb, v_current_lf, v_current_ws, u_current_nsbs, u_current_idw, u_current_if,u_current_lb, u_current_lf, u_current_ws
import processing
from .api.station import get_stations, StationApi, StationId, Station, Parameter
from .settings import DMISettingsManager, DMISettingKeys
warnings.simplefilter(action='ignore', category=FutureWarning)

# The lists that will be used for parameters, stations, municipalities, 10 and 20km grids in the API calls.
# Stations are not part of this list, as stations are more dynamicly added and removed.
# Stations are therefore imported from DMI Open Data via. the internet, each time QGIS is started.
from .para_munic_grid import para_grid, grid10, grid20, munic

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
# Ignore this, we no longer use the static ui files, look at pluginui_test.py instead
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'DMI_Open_Data_dialog_base.ui'))
########### DELETE ##############


# This is where you import and inherit your PY UI class
class DMIOpenDataDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, settings_manager: DMISettingsManager, parent=None):
        """Constructor."""
        super(DMIOpenDataDialog, self).__init__(parent)
        self.settings_manager = settings_manager
        load_ui_options = {}
        try:
            self.stations_ocean, self.oceanobs_parameters = self.get_stations_and_parameters_if_settings_allow(
                StationApi.OCEAN_OBS,
                DMISettingKeys.OCEANOBS_API_KEY
            )
        except Exception as ex:
            self.stations_ocean, self.oceanobs_parameters = {}, {}
            QMessageBox.warning(self, self.tr("DMI Open Data"),
                                self.tr(str(ex)))
            load_ui_options['invalid_oceanobs_api_key'] = True
        try:
            self.stations_climate, self.climatedata_parameters = self.get_stations_and_parameters_if_settings_allow(
                StationApi.CLIMATE_STATION_VALUE,
                DMISettingKeys.CLIMATEDATA_API_KEY
            )
        except Exception as ex:
            self.stations_climate, self.climatedata_parameters = {}, {}
            QMessageBox.warning(self, self.tr("DMI Open Data"),
                                self.tr(str(ex)))
            load_ui_options['invalid_climate_api_key'] = True
        try:
            self.stations_metobs, self.metobs_parameters = self.get_stations_and_parameters_if_settings_allow(
                StationApi.MET_OBS,
                DMISettingKeys.METOBS_API_KEY
            )
        except Exception as ex:
            self.stations_metobs, self.metobs_parameters = {}, {}
            QMessageBox.warning(self, self.tr("DMI Open Data"),
                                self.tr(str(ex)))
            load_ui_options['invalid_metobs_api_key'] = True

        super(DMIOpenDataDialog, self).setupUi(self)
        self.load_station_and_parameter_ui(**load_ui_options)

        # All the radiobuttons that by default is checked
        self.stat_type.setChecked(True)
        self.hour_climate.setChecked(True)
        self.met_stat_info.setChecked(True)
        self.radioButton_4.setChecked(True)
        self.radioButton_10.setChecked(True)
        self.radioButton_9.setChecked(True)
        self.radioButton_14.setChecked(True)
        self.radioButton_19.setChecked(True)
        self.radioButton_21.setChecked(True)
        self.wam_fore.setChecked(True)
        self.north_sea_baltic_sea.setChecked(True)
        self.danish_waters.setChecked(True)
        #self.all_para_dkss.setChecked(True)
        #self.all_para_wam.setChecked(True)
        self.dev_sea_mean.setChecked(True)
        self.wind_speed_10.setChecked(True)
        self.composite.setChecked(True)
        self.full_range.setChecked(True)
        self._60960.setChecked(True)
        self.all_lightning_types.setChecked(True)


        # Datetime default today and yesterday
        self.start_date.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.end_date.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.climate_data_start_date_dateedit.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.climate_data_end_date_dateedit.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.radar_start_date.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(23, 50, 0)))
        self.radar_end_date.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.lightning_start_date.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.lightning_end_date.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.datetime_fore_start.setDateTime(QDateTime(QDate.currentDate().addDays(1), QTime(22, 00, 0)))
        self.datetime_fore_end.setDateTime(QDateTime(QDate.currentDate().addDays(2), QTime(0, 0, 0)))

        self.start_date5.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.end_date5.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.dateTimeEdit.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.dateTimeEdit_2.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.dateTimeEdit_3.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.dateTimeEdit_4.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        # All the buttons that do actions
        self.run_app.clicked.connect(self.run)
        self.browse_obs.clicked.connect(self.browse_files_obs)
        self.browse_cli.clicked.connect(self.browse_files_cli)
        self.browse_lig.clicked.connect(self.browse_files_lig)
        self.browse_oce.clicked.connect(self.browse_files_oce)
        self.stat_type.clicked.connect(self.stat_typeR)
        self.grid10_type.clicked.connect(self.grid10_typeR)
        self.grid20_type.clicked.connect(self.grid20_typeR)
        self.munic_type.clicked.connect(self.municipality_typeR)
        self.country_type.clicked.connect(self.country_typeR)
        self.dmi_open_data.clicked.connect(self.open_openData)
        self.dmi_open_data_2.clicked.connect(self.open_openData_2)
        self.dmi_dk.clicked.connect(self.open_dmi_dk)
        self.stackedWidget.setCurrentWidget(self.stat_clima)
        self.stackedWidget_2.setCurrentWidget(self.stat_para)
        self.stackedWidget_3.setCurrentWidget(self.met_stat_page)
        self.met_stat_info.clicked.connect(self.infoStat)
        self.para_stacked.setCurrentWidget(self.wam_page)
        self.stackedWidget_4.setCurrentWidget(self.nsbs_depth)
        self.wam_fore.clicked.connect(self.wamTab)
        self.dkss_fore.clicked.connect(self.dkssTab)
        self.tide_info.clicked.connect(self.infoTide)
        self.radioButton_10.clicked.connect(self.disable_time)
        self.radioButton_11.clicked.connect(self.enable_time)
        self.radioButton_21.clicked.connect(self.disable_time_oce)
        self.radioButton_22.clicked.connect(self.enable_time_oce)
        self.north_sea_baltic_sea.clicked.connect(self.nsbs_depth_tab)
        self.inner_danish_waters.clicked.connect(self.idw_depth_tab)
        self.wadden_sea.clicked.connect(self.ws_depth_tab)
        self.isefjord.clicked.connect(self.if_depth_tab)
        self.limfjord.clicked.connect(self.lf_depth_tab)
        self.little_belt.clicked.connect(self.lb_depth_tab)
        self.dev_sea_mean.clicked.connect(self.depth_tab_dis)
        self.u_comp_wind.clicked.connect(self.depth_tab_dis)
        self.v_comp_wind.clicked.connect(self.depth_tab_dis)
        self.u_comp_cur.clicked.connect(self.depth_tab_dis)
        self.v_comp_cur.clicked.connect(self.depth_tab_dis)
        self.water_temp.clicked.connect(self.depth_tab_dis)
        self.salinity.clicked.connect(self.depth_tab_dis)
        self.ice_thick.clicked.connect(self.depth_tab_dis)
        self.ice_conc.clicked.connect(self.depth_tab_dis)
        self.u_comp_cur_.clicked.connect(self.depth_tab_enabled)
        self.v_comp_cur_.clicked.connect(self.depth_tab_enabled)
        self.water_temp_.clicked.connect(self.depth_tab_enabled)
        self.salinity_.clicked.connect(self.depth_tab_enabled)
        self.composite.clicked.connect(self.comp)
        self.pseudo.clicked.connect(self.pseud)

        # Sets the time in "Stations and parameters" unavailable untill "Defined Time" has been checked
        self.groupBox_25.setEnabled(False)
        self.groupBox_26.setEnabled(False)
        self.dateTimeEdit_3.setEnabled(False)
        self.dateTimeEdit_4.setEnabled(False)

        self.groupBox_14.setEnabled(False)

        self.stat_radar.setEnabled(False)

        self.radar_disable_if_needed()
        self.lightning_disable_if_needed()
        self.metobs_disable_if_needed()
        self.climate_disable_if_needed()
        self.ocean_disable_if_needed()
        self.forecast_disable_if_needed()
        self.stat_info_disable_if_needed()

    # Disables data-tab if no API key has been entered
    def stat_info_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.METOBS_API_KEY.value)
        if api_key == '':
            layout = self.tab_8.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.METOBS_API_KEY))
            self.tab_8.setEnabled(False)

    def forecast_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.FORECASTDATA_API_KEY.value)
        if api_key == '':
            layout = self.tab_4.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.FORECASTDATA_API_KEY))
            self.tab_4.setEnabled(False)

    def ocean_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.OCEANOBS_API_KEY.value)
        if api_key == '':
            layout = self.tab_5.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.OCEANOBS_API_KEY))
            self.tab_5.setEnabled(False)

    def radar_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.RADARDATA_API_KEY.value)
        if api_key == '':
            layout = self.tab_3.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.RADARDATA_API_KEY))
            self.tab_3.setEnabled(False)

    def lightning_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.LIGHTNINGDATA_API_KEY.value)
        if api_key == '':
            layout = self.lightning_tab.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.LIGHTNINGDATA_API_KEY))
            self.lightning_tab.setEnabled(False)

    def metobs_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.METOBS_API_KEY.value)
        if api_key == '':
            layout = self.tab.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.METOBS_API_KEY))
            self.tab.setEnabled(False)

    def climate_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.CLIMATEDATA_API_KEY.value)
        if api_key == '':
            layout = self.tab_2.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.CLIMATEDATA_API_KEY))
            self.tab_2.setEnabled(False)

    def get_stations_and_parameters_if_settings_allow(self, station_type: StationApi, settings_key: DMISettingKeys) -> Tuple[Dict[StationId, Station], Set[str]]:
        api_key = self.settings_manager.value(settings_key.value)
        stations = []
        parameters = {}
        if api_key:
            stations = get_stations(station_type, api_key)
            parameters = {parameter for station in stations.values() for parameter in station.parameters }
        return stations, parameters

    def load_station_and_parameter_ui(self, invalid_metobs_api_key=False, invalid_oceanobs_api_key=False, invalid_climate_api_key=False):
        # Creates the checkboxes for parameters in metObs
        self.listCheckBox_para_stat_metObs = \
            self.display_parameters(self.metobs_parameters, DMISettingKeys.METOBS_API_KEY, self.scrollAreaWidgetContents_2, invalid_api_key=invalid_metobs_api_key)
        # Creates checkboxes for stations in metobs
        self.listCheckBox_stat_metObs = \
            self.display_stations(self.stations_metobs, DMISettingKeys.METOBS_API_KEY, self.scrollAreaWidgetContents_3, invalid_api_key=invalid_metobs_api_key)
        # Creates the checkboxes for parameters in climateData
        self.listCheckBox_para_stat_climate = \
            self.display_parameters(self.climatedata_parameters, DMISettingKeys.CLIMATEDATA_API_KEY, self.scrollAreaWidgetContents_6, invalid_api_key=invalid_climate_api_key)
        # Creates the checkboxes for parameters used for grid, municipality and country
        self.listCheckBox_para_grid = \
            self.display_parameters(para_grid, DMISettingKeys.CLIMATEDATA_API_KEY, self.scrollAreaWidgetContents_8, invalid_api_key=invalid_climate_api_key)
        # Creates the checkboxes for stations in climateData
        self.listCheckBox_station_climate = \
            self.display_stations(self.stations_climate, DMISettingKeys.CLIMATEDATA_API_KEY, self.scrollAreaWidgetContents_5, invalid_api_key=invalid_climate_api_key)
        # Creates the checkboxes for cellIds in climateData
        self.listCheckBox_grid10 = \
            self.display_parameters(grid10, DMISettingKeys.CLIMATEDATA_API_KEY, self.scrollAreaWidgetContents, invalid_api_key=invalid_climate_api_key)
        # Creates the checkboxes for cellids in climateData
        self.listCheckBox_grid20 = \
            self.display_parameters(grid20, DMISettingKeys.CLIMATEDATA_API_KEY, self.scrollAreaWidgetContents_4, invalid_api_key=invalid_climate_api_key)
        # Creates the checkboxes for municipalities in climateData
        self.listCheckBox_municipalityId = \
            self.display_parameters(munic, DMISettingKeys.CLIMATEDATA_API_KEY, self.scrollAreaWidgetContents_7, invalid_api_key=invalid_climate_api_key)
        # Creates the checkboxes for stations in oceanObs
        self.listCheckBox_stat_ocean = \
            self.display_stations(self.stations_ocean, DMISettingKeys.OCEANOBS_API_KEY, self.scrollAreaWidgetContents_10, invalid_api_key=invalid_oceanobs_api_key)
        self.listCheckBox_station_climate_information = \
            self.display_parameters(self.climatedata_parameters, DMISettingKeys.METOBS_API_KEY,
                                    self.scrollAreaWidgetContents_9, invalid_api_key=invalid_climate_api_key, use_radio_button=True)

    @staticmethod
    def generate_no_api_key_label(settings_key: DMISettingKeys):
        return QtWidgets.QLabel(f'No API key configured for {settings_key.get_api_name()}\nPlease go to Settings -> Options -> DMI Open Data to configure')

    def display_stations(self, stations: Dict[StationId, Station], settings_key: DMISettingKeys, checkbox_container: QtWidgets.QScrollArea, invalid_api_key=False) -> Dict[StationId, QtWidgets.QCheckBox]:
        checkboxes = {}
        station_layout = checkbox_container.findChildren(QtWidgets.QVBoxLayout)[0]
        api_key = self.settings_manager.value(settings_key.value)
        if api_key and not invalid_api_key:
            for station_id, station in sorted(stations.items()):
                station_checkbox_widget = QtWidgets.QCheckBox(checkbox_container)
                station_checkbox_widget.setObjectName(station_id)
                station_checkbox_widget.setText(f'{station_id} {station.station_name}')
                checkboxes[station_id] = station_checkbox_widget
                station_layout.addWidget(station_checkbox_widget)
        else:
            station_layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(settings_key))
        return checkboxes

    def display_parameters(self, parameters: Set[Parameter], settings_key: DMISettingKeys, checkbox_container: QtWidgets.QScrollArea, invalid_api_key=False, use_radio_button=False) -> Dict[Parameter, QtWidgets.QCheckBox]:
        checkboxes = {}
        parameter_layout = checkbox_container.findChildren(QtWidgets.QVBoxLayout)[0]
        api_key = self.settings_manager.value(settings_key.value)
        if api_key and not invalid_api_key:
            for parameter in sorted(parameters):
                if use_radio_button:
                    parameter_widget = QtWidgets.QRadioButton(checkbox_container)
                else:
                    parameter_widget = QtWidgets.QCheckBox(checkbox_container)
                # Parameters are only unique per API, mixing in settings key to make globally unique object name
                parameter_widget.setObjectName(f"{settings_key}-{parameter}")
                parameter_widget.setText(parameter)
                checkboxes[parameter] = parameter_widget
                parameter_layout.addWidget(parameter_widget)
        else:
            parameter_layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(settings_key))
        return checkboxes

    def comp(self):
        self.stat_radar.setEnabled(False)
        self.scan_type.setEnabled(True)
    def pseud(self):
        self.stat_radar.setEnabled(True)
        self.scan_type.setEnabled(False)
# Disables or enables time in "Stations and parameters"
    def disable_time_oce(self):
        self.dateTimeEdit_3.setEnabled(False)
        self.dateTimeEdit_4.setEnabled(False)
    def enable_time_oce(self):
        self.dateTimeEdit_3.setEnabled(True)
        self.dateTimeEdit_4.setEnabled(True)
    def disable_time(self):
        self.groupBox_25.setEnabled(False)
        self.groupBox_26.setEnabled(False)
    def enable_time(self):
        self.groupBox_25.setEnabled(True)
        self.groupBox_26.setEnabled(True)
# Changes pages when clicked
    def wamTab(self):
        self.para_stacked.setCurrentWidget(self.wam_page)
    def dkssTab(self):
        self.para_stacked.setCurrentWidget(self.dkss_page)
    def depth_tab_dis(self):
        self.groupBox_14.setEnabled(False)
    def depth_tab_enabled(self):
        self.groupBox_14.setEnabled(True)
    def infoStat(self):
        self.stackedWidget_3.setCurrentWidget(self.met_stat_page)
    def infoGrid10(self):
        self.stackedWidget_3.setCurrentWidget(self.climate_page)
    def infoGrid20(self):
        self.stackedWidget_3.setCurrentWidget(self.climate_page)
    def infoMunic(self):
        self.stackedWidget_3.setCurrentWidget(self.climate_page)
    def infoRadar(self):
        self.stackedWidget_3.setCurrentWidget(self.radar_page)
    def infoLight(self):
        self.stackedWidget_3.setCurrentWidget(self.light_page)
    def infoTide(self):
        self.stackedWidget_3.setCurrentWidget(self.tide_page)
    def nsbs_depth_tab(self):
        self.stackedWidget_4.setCurrentWidget(self.nsbs_depth)
    def idw_depth_tab(self):
        self.stackedWidget_4.setCurrentWidget(self.idw_depth)
    def ws_depth_tab(self):
        self.stackedWidget_4.setCurrentWidget(self.ws_depth)
    def if_depth_tab(self):
        self.stackedWidget_4.setCurrentWidget(self.if_depth)
    def lf_depth_tab(self):
        self.stackedWidget_4.setCurrentWidget(self.lf_depth)
    def lb_depth_tab(self):
        self.stackedWidget_4.setCurrentWidget(self.lb_depth)



# Actions for buttons to go to dmi.dk
    def open_openData(self):
        webbrowser.open('https://confluence.govcloud.dk/display/FDAPI/Danish+Meteorological+Institute+-+Open+Data')
    def open_openData_2(self):
        webbrowser.open('https://confluence.govcloud.dk/display/FDAPI/Danish+Meteorological+Institute+-+Open+Data')
    def open_dmi_dk(self):
        webbrowser.open('https://www.dmi.dk/')
# Actions when saving as .csv
    def browse_files_cli(self):
        fname = QFileDialog.getSaveFileName(self, 'Open File', 'C:')
        self.file_name_cli.setText(fname[0])
    def browse_files_lig(self):
        fname = QFileDialog.getSaveFileName(self, 'Open File', 'C:')
        self.file_name_lig.setText(fname[0])
    def browse_files_oce(self):
        fname = QFileDialog.getSaveFileName(self, 'Open File', 'C:')
        self.file_name_oce.setText(fname[0])
# Changing pages in Climate Data
    def stat_typeR(self):
        self.stackedWidget.setCurrentWidget(self.stat_clima)
        self.stackedWidget_2.setCurrentWidget(self.stat_para)
    def grid10_typeR(self):
        self.stackedWidget.setCurrentWidget(self.grid_10)
        self.stackedWidget_2.setCurrentWidget(self.grid_para)
    def grid20_typeR(self):
        self.stackedWidget.setCurrentWidget(self.grid_20)
        self.stackedWidget_2.setCurrentWidget(self.grid_para)
    def municipality_typeR(self):
        self.stackedWidget.setCurrentWidget(self.municipality)
        self.stackedWidget_2.setCurrentWidget(self.grid_para)
    def country_typeR(self):
        self.stackedWidget.setCurrentWidget(self.country)
        self.stackedWidget_2.setCurrentWidget(self.grid_para)
    def browse_files_obs(self):
        fname = QFileDialog.getSaveFileName(self, 'Open File', 'C:')
        self.file_name_obs.setText(fname[0])

    def run(self):
        parameters = []
        stations = []

        index = self.tabWidget.currentIndex()
        # dataName is used to define which type of data the user is interested in
        # (metObs, climateData, radar, oceanData,lightnign)
        dataName = self.tabWidget.tabText(index)
        # Based on dataName, data_type and API key are asigned
        # data_type is the service name used in URL creation
        if dataName == 'Meteorological Observations':
            data_type = 'metObs'
            api_key = self.settings_manager.value(DMISettingKeys.METOBS_API_KEY.value)
        elif dataName == 'Oceanographic Observations':
            data_type = 'oceanObs'
            api_key = self.settings_manager.value(DMISettingKeys.OCEANOBS_API_KEY.value)
        elif dataName == 'Radar Data':
            data_type = 'radardata'
            api_key = self.settings_manager.value(DMISettingKeys.RADARDATA_API_KEY.value)
        elif dataName == 'Climate Data':
            data_type = 'climateData'
            api_key = self.settings_manager.value(DMISettingKeys.CLIMATEDATA_API_KEY.value)
        elif dataName == 'Lightning Data':
            data_type = 'lightningdata'
            api_key = self.settings_manager.value(DMISettingKeys.LIGHTNINGDATA_API_KEY.value)
        elif dataName == 'Forecast Data':
            data_type = 'forecastdata'
            api_key = self.settings_manager.value(DMISettingKeys.FORECASTDATA_API_KEY.value)
        elif dataName == 'Stations and Parameters' and self.met_stat_info.isChecked():
            data_type = 'stat_para_info'
        elif dataName == 'Stations and Parameters' and self.tide_info.isChecked():
            data_type = 'ocean_para_info'
        
        # data_type and data_type2 are assigned
        # data_type2 is the type of collection and will be assigned based on the users preferences.
        # climateData has multiple types of collection
        if data_type == 'oceanObs' or data_type == 'metObs' or data_type == 'lightningdata':
            data_type2 = 'observation'
        elif data_type == 'climateData':
            if self.grid10_type.isChecked():
                data_type2 = '10kmGridValue'
            elif self.grid20_type.isChecked(): 
                data_type2 = '20kmGridValue'
            elif self.munic_type.isChecked(): 
                data_type2 = 'municipalityValue'
            elif self.country_type.isChecked():
                data_type2 = 'countryValue'
            elif self.stat_type.isChecked():
                data_type2 = 'stationValue'
        elif data_type == 'radardata':
            if self.composite.isChecked():
                data_type2 = 'composite'
            elif self.pseudo.isChecked():
                data_type2 = 'pseudoCappi'
        elif data_type == '':
            data_type2 = ''
        elif data_type == 'stat_para_info':
            data_type2 = 'climateData'
        elif data_type == 'ocean_para_info':
            data_type2 = 'oceanObs'
        elif data_type == 'forecastdata':
            if self.wam_fore.isChecked():
                data_type2 = 'wam'
            elif self.dkss_fore.isChecked():
                data_type2 = 'dkss'


        # Based on data_type2 the stationId, municipalityId or cellId will be assigned.
        if data_type2 == 'observation' and data_type == 'metObs':
            stat1 = 'stationId'
        elif data_type2 == 'observation' and data_type == 'oceanObs':
            stat1 = 'stationId'
        elif data_type2 == 'stationValue' and data_type == 'climateData':
            stat1 = 'stationId'
        elif data_type2 == 'municipalityValue':
            stat1 = 'municipalityId'
        elif data_type2 == '10kmGridValue':
            stat1 = 'cellId'
        elif data_type2 == '20kmGridValue':
            stat1 = 'cellId'
        elif data_type2 == 'wam':
            if self.danish_waters.isChecked():
                fore_area = 'dw'
            elif self.north_atlantic.isChecked():
                fore_area = 'natlant'
            elif self.north_sea_baltic.isChecked():
                fore_area = 'nsb'
        elif data_type2 == 'dkss':
            if self.north_sea_baltic_sea.isChecked():
                fore_area = 'nsbs'
            elif self.inner_danish_waters.isChecked():
                fore_area = 'idw'
            elif self.wadden_sea.isChecked():
                fore_area = 'ws'
            elif self.isefjord.isChecked():
                fore_area = 'if'
            elif self.limfjord.isChecked():
                fore_area = 'lf'
            elif self.little_belt.isChecked():
                fore_area = 'lb'

        # Oceanographic parameters
        if dataName == 'Oceanographic Observations':
            if self.sealev_dvr.isChecked():
                parameters.append('sealev_dvr')
                self.sealev_dvr.setChecked(False)
            if self.sealev_ln.isChecked():
                parameters.append('sealev_ln')
                self.sealev_ln.setChecked(False)
            if self.sea_reg.isChecked():
                parameters.append('sea_reg')
                self.sea_reg.setChecked(False)
            if self.tw.isChecked():
                parameters.append('tw')
                self.tw.setChecked(False)

        # Oceanographic stations
        if dataName == 'Oceanographic Observations':
            for ocean_station_id in self.stations_ocean.keys():
                qt_checkbox_widget = self.listCheckBox_stat_ocean[ocean_station_id]
                if qt_checkbox_widget.isChecked():
                    stations.append(ocean_station_id)
                    qt_checkbox_widget.setChecked(False)

        # Climate stations
        if data_type2 == 'stationValue':
            for climate_station_id in self.stations_climate.keys():
                qt_checkbox_widget = self.listCheckBox_station_climate[climate_station_id]
                if qt_checkbox_widget.isChecked():
                    stations.append(climate_station_id)
                    qt_checkbox_widget.setChecked(False)
        
        # 10 km grid cells
        if data_type2 == '10kmGridValue':
            for grid10_id in grid10:
                qt_checkbox_widget = self.listCheckBox_grid10[grid10_id]
                if qt_checkbox_widget.isChecked():
                    stations.append(grid10_id)
                    qt_checkbox_widget.setChecked(False)

        # 20 km grid cells
        if data_type2 == '20kmGridValue':
            for grid20_id in grid20:
                qt_checkbox_widget = self.listCheckBox_grid20[grid20_id]
                if qt_checkbox_widget.isChecked():
                    stations.append(grid20_id)
                    qt_checkbox_widget.setChecked(False)

        # Municipality ID
        if data_type2 == 'municipalityValue':
            for munic_id in munic:
                qt_checkbox_widget = self.listCheckBox_municipalityId[munic_id]
                if qt_checkbox_widget.isChecked():
                    stations.append(munic_id)
                    qt_checkbox_widget.setChecked(False)

        # Grid, municipality and country parameters
        if data_type2 == 'municipalityValue'or data_type2 == '20kmGridValue' or data_type2 == '10kmGridValue' or data_type2 == 'countryValue':
            for p_g in para_grid:
                qt_checkbox_widget = self.listCheckBox_para_grid[p_g]
                if qt_checkbox_widget.isChecked():
                    parameters.append(p_g)
                    qt_checkbox_widget.setChecked(False)

        # Climate stations parameters
        if data_type2 == 'stationValue':
            for parameter in self.climatedata_parameters:
                qt_checkbox_widget = self.listCheckBox_para_stat_climate[parameter]
                if qt_checkbox_widget.isChecked():
                    parameters.append(parameter)
                    qt_checkbox_widget.setChecked(False)
            
        # metObs stations
        if dataName == 'Meteorological Observations':
            for stationId in self.stations_metobs.keys():
                qt_checkbox_widget = self.listCheckBox_stat_metObs[stationId]
                if qt_checkbox_widget.isChecked():
                    stations.append(stationId)
                    qt_checkbox_widget.setChecked(False)

        # metObs parameters
        if dataName == 'Meteorological Observations':
            for parameter in self.metobs_parameters:
                qt_checkbox_widget = self.listCheckBox_para_stat_metObs[parameter]
                if qt_checkbox_widget.isChecked():
                    parameters.append(parameter)
                    qt_checkbox_widget.setChecked(False)

        if data_type2 == 'wam':
            wam_para = ['wind_speed_10', 'wind_direction_10', 'sig_wave_height', 'dom_wave_period', 'mean_wave_period',
                        'mean_zero_wave_period', 'mean_wave_dir', 'sig_height_wind_waves_sea', 'mean_period_wind_wave_sea',
                        'mean_dir_wind_wave_sea', 'sig_height_swell', 'mean_period_swell', 'mean_dir_swell',
                        'benjamin_index']
            wam_para_band = list(range(1, 15))
            para_fore_dict_wam = dict(zip(wam_para, wam_para_band))
            for fore_para in para_fore_dict_wam:
                qt_checkbox_widget = getattr(self, fore_para)
                if qt_checkbox_widget.isChecked():
                    parameters.append(fore_para)
                    qt_checkbox_widget.setChecked(False)

        if data_type2 == 'dkss':
            nsbs_para = ['dev_sea_mean', 'u_comp_wind', 'v_comp_wind', 'u_comp_cur', 'v_comp_cur',
                         'water_temp', 'salinity', 'ice_thick', 'ice_conc', 'u_comp_cur_',
                         'v_comp_cur_', 'water_temp_', 'salinity_']
            nsbs_para_band = list(range(1, 10))
            para_fore_dict_nsbs = dict(zip(nsbs_para[0:9], nsbs_para_band))
            for fore_para in nsbs_para:
               qt_checkbox_widget = getattr(self, fore_para)
               if qt_checkbox_widget.isChecked():
                   parameters.append(fore_para)
                   qt_checkbox_widget.setChecked(False)
                    
        # Information for stations. The list of stations is based on climateData and NOT metObs
        if dataName == 'Stations and Parameters' and data_type2 == 'climateData':
            for parameter in self.climatedata_parameters:
                qt_checkbox_widget = self.listCheckBox_station_climate_information[parameter]
                if qt_checkbox_widget.isChecked():
                    parameters.append(parameter)
                    qt_checkbox_widget.setChecked(False)
        if dataName == 'Stations and Parameters' and data_type2 == 'oceanObs':
            ocean_parameters = ['sea_reg_info', 'sealev_dvr_info', 'sealev_ln_info', 'tw_info']
            for oce_para in ocean_parameters:
                qt_checkbox_widget = getattr(self, oce_para)
                if qt_checkbox_widget.isChecked():
                    parameters.append(oce_para[:-5])
                    qt_checkbox_widget.setChecked(False)

        if dataName == 'Radar Data' and data_type2 == 'pseudoCappi':
            radar_stations_it  = []
            radar_stations = ['_60960', '_06036', '_06194', '_06177', '_06103']
            for radar_stat in radar_stations:
                qt_checkbox_widget = getattr(self, radar_stat)
                if qt_checkbox_widget.isChecked():
                    radar_stations_it.append(radar_stat[1:])
                    qt_checkbox_widget.setChecked(False)
        # Datetime
        # Changes the format of the datetime to make it compatible for the URL calls.
        # The format by QT is yyyy:m:d h:m:s and the format needed for URL is yyyy:mm:ddThh:mm:ssZ
        if dataName == 'Meteorological Observations':
            start_datetime = self.start_date.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.end_date.dateTime().toString(Qt.ISODate) + 'Z'
            
        elif dataName == 'Climate Data':
            start_datetime = self.climate_data_start_date_dateedit.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.climate_data_end_date_dateedit.dateTime().toString(Qt.ISODate) + 'Z'
            
        elif dataName == 'Radar Data':
            start_datetime = self.radar_start_date.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.radar_end_date.dateTime().toString(Qt.ISODate) + 'Z'

        elif dataName == 'Lightning Data':
            start_datetime = self.lightning_start_date.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.lightning_end_date.dateTime().toString(Qt.ISODate) + 'Z'

        elif dataName == 'Oceanographic Observations':
            start_datetime = self.start_date5.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.end_date5.dateTime().toString(Qt.ISODate) + 'Z'

        elif dataName == 'Forecast Data':
            start_datetime = self.datetime_fore_start.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.datetime_fore_end.dateTime().toString(Qt.ISODate) + 'Z'

        elif dataName == 'Stations and Parameters' and data_type2 == 'climateData':
            start_datetime = self.dateTimeEdit.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.dateTimeEdit_2.dateTime().toString(Qt.ISODate) + 'Z'

        elif dataName == 'Stations and Parameters' and data_type2 == 'oceanObs':
            start_datetime = self.dateTimeEdit_3.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.dateTimeEdit_4.dateTime().toString(Qt.ISODate) + 'Z'

        datetime = start_datetime + '/' + end_datetime

        if start_datetime > end_datetime:
            if dataName == 'Stations and Parameters':
                pass
            else:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                 self.tr('Start time is after end time.'))
                return

        # A list that holds all stations that doesnt meet the requirement set by the user.
        error_stats = []

        # URL creation for metObs and climateData
        # Resolution
        if self.hour_climate.isChecked():
            res = 'hour'
        elif self.day_climate.isChecked():
            res = 'day'
        elif self.month_climate.isChecked():
            res = 'month'
        elif self.year_climate.isChecked():
            res = 'year'
        # URL call and pandas creation
        if data_type2 == 'countryValue':
            stations.append('Denmark')
            stat1 = 'Denmark'
        # Errors if no stations or parameters chosen.
        # When 0 is assigned to observations_count, it means that the program shouldnt run further, as there is an issue with data.
        # num is only used in climateData, metObs and oceanObs.
        if dataName == 'Climate Data' or dataName == 'Meteorological Observations' or dataName == 'Oceanographic Observations':
            if len(stations) == 0:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('Please select a station.'))
                observations_count = 0
            if len(parameters) == 0:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('Please select a parameter.'))
                observations_count = 0

        # A pandas DataFrame is created to easier manage the data, and to convert to csv.
        station_table = pd.DataFrame()
        # Iterates over each station that has been checked by the user.
        # It is only possible to check stations in climateData, metObs and oceanObs. This section is therefor only for these 3.
        for stat in stations:
            station_total_observations = 0
            url = 'https://dmigw.govcloud.dk/v2/' + data_type + '/collections/' + data_type2 + '/items'
            # Will be initialized later, when the merge column is known
            station_param_table = pd.DataFrame()
            # Iterates over all the parameters that has been checked by the user.
            for para in parameters:
                params = {'api-key': api_key,
                          'datetime': datetime,
                          'parameterId': para,
                          'limit': '300000'}
                if dataName == 'Climate Data' and data_type2 != 'countryValue':
                    stat_and_res = {stat1 : stat,
                                    'timeResolution': res}
                    params.update(stat_and_res)
# No stations for country values.
                elif dataName == 'Climate Data' and data_type2 == 'countryValue':
                    res_country = {'timeResolution': res}
                    params.update(res_country)
                else:
                    observed_w_stat = {stat1 : stat}
                    params.update(observed_w_stat)
                r = requests.get(url, params=params)  
                print(r.url)
                json = r.json()
                #df = json_normalize(json['features'])
                # Makes sure that data gets a return. If no numbers returned then shows a warning box.
                # r_code represents the status code.
                r_code = r.status_code
                # 403 means that the api is wrong.
                if r_code == 403:
                    observations_count = 0
                    QMessageBox.warning(self, self.tr("DMI Open Data"), self.tr('API Key is not valid or is expired / revoked.'))
                # if the call has the right API, then continue. This does not mean that the call will deliver data!
                # The station could still not be measuring the wished parameter.
                elif r_code != 403:
                    observations_count = json['numberReturned']
                    station_total_observations += observations_count
                if observations_count > 0:
                    df = json_normalize(json['features'])
                    new_param_table = pd.DataFrame({para: df['properties.value']})
                    if data_type2 == 'observation':
                        new_param_table['observed'] = df['properties.observed']
                        merge_column = ['observed']
                    elif data_type == 'climateData':
                        new_param_table['from'] = df['properties.from']
                        new_param_table['to'] = df['properties.to']
                        merge_column = ['from', 'to']
                    if stat1 == 'stationId':
                        merge_column += [stat1]
                        new_param_table[stat1] = df['properties.stationId']
                    elif stat1 == 'cellId':
                        merge_column += [stat1]
                        new_param_table[stat1] = df['properties.cellId']
                    elif stat1 == 'municipalityId':
                        merge_column += [stat1]
                        new_param_table[stat1] = df['properties.municipalityId']
                    if station_param_table.empty:
                        station_param_table = new_param_table
                    else:
                        station_param_table = station_param_table.merge(new_param_table, how='outer', on=merge_column)
                # If the API is correct but the chosen parameter is not measured by the station.
                elif observations_count == 0 and r_code != 403:
                    error_stats.append(stat)
            if station_total_observations > 0:
                # Changes the name of the header and adds it to the new dataframe
                if data_type2 == 'observation':
                    df['properties.observed'] = pd.to_datetime(df['properties.observed'])
                elif data_type == 'climateData':
                    df['properties.from'] = pd.to_datetime(df['properties.from'])

                if station_table.empty:
                    station_table = station_param_table
                else:
                    station_table = station_table.merge(
                        station_param_table,
                        how='outer',
                        on=list(set(station_table.columns) & set(station_param_table.columns))
                    )
                # QGIS geometry
                # The coordinate for the station
                coordinates = df['geometry.coordinates'].iloc[0]
                # Name and geometry type for the layer
                if stat1 == 'stationId':
                    vl = QgsVectorLayer("Point", stat, "memory")
                elif stat1 == 'municipalityId':
                    vl = QgsVectorLayer("Point", stat + ' ' + df['properties.municipalityName'].iloc[0], "memory")
                elif stat1 == 'cellId':
                    vl = QgsVectorLayer("Polygon", stat, "memory")
                elif stat1 == 'Denmark':
                    vl = QgsVectorLayer('Point', stat1, 'memory')
                pr = vl.dataProvider()
                vl.startEditing()
                # Gives headers in attribute table in QGIS
                for head in station_param_table:
                    if head in ['observed', 'from', 'to']:
                        pr.addAttributes([QgsField(head, QVariant.DateTime)])
                    if head == para:
                        pr.addAttributes([QgsField(head, QVariant.Double)])
                    elif head != 'observed':
                        pr.addAttributes([QgsField(head, QVariant.String)])
                vl.updateFields()
                f = QgsFeature()
                # Iterates over the rows in the df. This depends on the amount of parameters called.
                # Maximum numbers of parameters available is 7 because of this.
                # Cliamte data has 2 datetimes where metObs only has 1 which explains the following if statement.
                if dataName == 'Climate Data' and data_type2 != 'countryValue':
                    for row in station_param_table.itertuples():
                        listee = list(row[1:len(station_param_table.columns) + 1])
                        if stat1 == 'cellId':
                            koordi = [QgsPointXY(coordinates[0][0][0], coordinates[0][0][1]),
                                      QgsPointXY(coordinates[0][1][0], coordinates[0][1][1]), \
                                      QgsPointXY(coordinates[0][2][0], coordinates[0][2][1]),
                                      QgsPointXY(coordinates[0][3][0], coordinates[0][3][1]), \
                                      QgsPointXY(coordinates[0][4][0], coordinates[0][4][1])]
                            f.setGeometry(QgsGeometry.fromPolygonXY([koordi]))
                        elif stat1 != 'cellId':
                            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(coordinates[0], coordinates[1])))
                        f.setAttributes(listee)
                        vl.addFeature(f)
                elif data_type2 == 'observation' or data_type2 == 'countryValue':
                    for row in station_param_table.itertuples():
                        listee = list(row[1:len(station_param_table.columns)+1])
                        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(coordinates[0], coordinates[1])))
                        f.setAttributes(listee)
                        vl.addFeature(f)
                vl.updateExtents()
                vl.commitChanges()
                QgsProject.instance().addMapLayer(vl)
                iface.zoomToActiveLayer()
        # The files are saved, if the user has chosen to write something in the "save as .csv" section
        if dataName == 'Meteorological Observations':
            if self.file_name_obs.text() == '':
                pass
            else:
                station_table.to_csv(self.file_name_obs.text() + '.csv', index=False)
                self.file_name_obs.clear()
        elif dataName == 'Climate Data':
            if self.file_name_cli.text() == '':
                pass
            else:
                station_table.to_csv(self.file_name_cli.text() + '.csv', index=False)
                self.file_name_cli.clear()
        elif dataName == 'Oceanographic Observations':
            if self.file_name_oce.text() == '':
                pass
            else:
                station_table.to_csv(self.file_name_oce.text() + '.csv', index=False)
                self.file_name_oce.clear()
        # URL call radar data
        if dataName == 'Radar Data':
            root = QgsProject.instance().layerTreeRoot()
            layer_group = root.insertGroup(0, 'Radar ' + datetime)
            temp = mkdtemp(suffix='_radar-files')
            url = 'https://dmigw.govcloud.dk/v1/' + data_type + '/collections/' + data_type2 + '/items'
            params = {'api-key' : api_key,
                    'datetime' : datetime
                    }
            if self.composite.isChecked():
                if self.full_range.isChecked():
                    params.update({'scanType': 'fullRange'})
                elif self.doppler.isChecked():
                    params.update({'scanType': 'doppler'})
            elif self.pseudo.isChecked():
                params.update({'stationId': radar_stations_it})
            r = requests.get(url, params=params)
            print(r.url)
            r_code = r.status_code
            json = r.json()
            if r_code == 403:
                observations_count = 0
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('API Key is not valid or is expired / revoked.'))
            elif r_code != 403:
                observations_count = json['numberReturned']
            if observations_count == 0:
                QMessageBox.warning(self, self.tr("DMI Open Data"), self.tr('Radar data is only available 6 months prior to current date, and has a delay in upload. \
                Please change date and time.'))
            elif observations_count > 0:
                for feature in json['features']:
                    downloadurl = feature['asset']['data']['href']
                    downloaddata = requests.get(downloadurl)
                    id = feature['id']
                    tempfile = os.path.join(temp, id)
                    if not os.path.isfile(tempfile):
                        with open(tempfile, 'wb') as fd:
                            for chunk in downloaddata.iter_content(chunk_size=128):
                                fd.write(chunk)
                    layer = QgsRasterLayer(tempfile)
                    # Set layer tempral properties
                    if self.both_types.isChecked():
                        time_dif = 300
                    else:
                        time_dif = 600
                    layer.temporalProperties().setMode(QgsRasterLayerTemporalProperties.ModeFixedTemporalRange)
                    d = feature['properties']['datetime']
                    start_time = QDateTime.fromString(d, "yyyy-MM-ddThh:mm:ssZ")
                    end_time = start_time.addSecs(time_dif)
                    time_range = QgsDateTimeRange(start_time, end_time)
                    layer.temporalProperties().setFixedTemporalRange(time_range)
                    layer.temporalProperties().setIsActive(True)
                    # This removes all values below 1 and above 254, since this only consists of white and black fields.
                    layer.setContrastEnhancement(algorithm=QgsContrastEnhancement.ClipToMinimumMaximum,
                                                     limits=QgsRasterMinMaxOrigin.MinMax)
                    layer.renderer().contrastEnhancement().setMinimumValue(1)
                    layer.renderer().contrastEnhancement().setMaximumValue(254)
                    if data_type2 == 'composite' and self.both_types.isChecked() == False:
                        layer.setName(data_type2 +  ' ' + params['scanType'] + ' ' +  d)
                    elif self.both_types.isChecked() == True:
                        layer.setName(data_type2 + ' both types ' + d)
                    elif data_type2 == 'pseudoCappi':
                        layer.setName(data_type2 + ' ' + radar_stations_it[0] + ' ' + d)
                    project = QgsProject.instance()
                    project.addMapLayer(layer, addToLegend=False)
                    layer_group.insertLayer(-1, layer)

        # Lightning data URL creation
        if dataName == 'Lightning Data':
            url = 'https://dmigw.govcloud.dk/v2/' + data_type + '/collections/' + data_type2 + '/items'
            params = {'api-key' : api_key,
                    'datetime' : datetime,
                      'limit' : '300000'}
            # Did the user choose the BBOX?
            if self.bbox_lightning.text() != '':
                params.update({'bbox': self.bbox_lig.text()})
            # Did the user choose any specific lightning type?
            if self.cloud_to_g_pos.isChecked():
                params.update({'type': '1'})
                name = 'Lightning cloud to ground (positive)'
            elif self.cloud_to_g_neg.isChecked():
                params.update({'type': '0'})
                name = 'Lightning cloud to ground (negative)'
            elif self.cloud_to_cloud.isChecked():
                params.update({'type': '2'})
                name = 'Lightning cloud to cloud'
            else:
                name = 'Lightning'
            # URL creation
            r = requests.get(url, params=params)
            print(r.url)
            json = r.json()
            r_code = r.status_code
            if r_code == 403:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('API Key is not valid or is expired / revoked.'))
                observations_count = 0
            elif r_code != 403:
                observations_count = json['numberReturned']
                df = json_normalize(json['features'])
            if observations_count == 0 and r_code != 403:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('No lightnings observed. Change time or parameter.'))
            elif observations_count > 0:
                # QGIS geometry
                df = df.drop(['id','type','geometry.type','properties.created'], axis=1)
                vl = QgsVectorLayer("Point",name , "memory")
                for row in df.itertuples():
                    name = df['properties.observed']
                    pr = vl.dataProvider()
                    vl.startEditing()
                    f = QgsFeature()
                    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(row[1][0], row[1][1])))
                    for head in df:
                        if head != 'geometry.coordinates':
                            pr.addAttributes([QgsField(head, QVariant.String)])
                    vl.updateFields()
                    f.setAttributes([row[2],row[3],row[4],row[5],row[6]])
                    vl.addFeature(f)
                    vl.updateExtents()
                vl.commitChanges()
                QgsProject.instance().addMapLayer(vl)
                # Does the user want to save as csv?
                if self.file_name_lig.text() == '':
                    pass
                else:
                    df.to_csv(self.file_name_lig.text() + '.csv', index=False)
                    self.file_name_lig.clear()
        # Forecast data
        if dataName == 'Forecast Data':
            root = QgsProject.instance().layerTreeRoot()
            layer_group = root.insertGroup(0, 'Forecast' + datetime)
            temp = mkdtemp(suffix='_forecast-files')
            url = 'https://dmigw.govcloud.dk/v1/' + data_type + '/collections/' + data_type2 + '_' + fore_area + '/items'
            params = {'api-key': api_key,
                    'datetime': datetime,
                    'limit': '300000'}
            if self.bbox_fore.text() != '':
                params.update({'bbox': self.bbox_fore.text()})
            r = requests.get(url, params=params)
            print(r, r.url)
            json = r.json()
            latest_model_run = sorted(json['features'], key=lambda feature: feature['properties']['modelRun'])[-1]['properties']['modelRun']
            print(latest_model_run)
            for feature in filter(lambda feature: feature['properties']['modelRun'] == latest_model_run, json['features']):
                downloadurl = feature['asset']['data']['href']
                downloaddata = requests.get(downloadurl)
                id = feature['id']
                print(id)
                tempfile = os.path.join(temp, id)
                if not os.path.isfile(tempfile):
                    with open(tempfile, 'wb') as fd:
                        for chunk in downloaddata.iter_content():
                            fd.write(chunk)
                layer = QgsRasterLayer(tempfile)
                #if self.all_para_wam.isChecked() == False or self.all_para_dkss.isChecked() == False:
                if data_type2 == 'wam':
                    band_par = para_fore_dict_wam[parameters[0]]
                    print(band_par)
                elif data_type2 == 'dkss':
                    if parameters[0] in depth_para_dkss:
                        if fore_area == 'nsbs':
                            depth = int(self.depth_box_nsbs.currentText())
                            if parameters[0] == 'salinity_':
                                band_par = salinity_nsbs[depth]
                            elif parameters[0] == 'water_temp_':
                                band_par = water_temp_nsbs[depth]
                            elif parameters[0] == 'v_comp_cur_':
                                band_par = u_current_nsbs[depth]
                            elif parameters[0] == 'u_comp_cur_':
                                band_par = v_current_nsbs[depth]
                        elif fore_area == 'idw':
                            depth = int(self.depth_box_idw.currentText())
                            if parameters[0] == 'salinity_':
                                band_par = salinity_idw[depth]
                            elif parameters[0] == 'water_temp_':
                                band_par = water_temp_idw[depth]
                            elif parameters[0] == 'v_comp_cur_':
                                band_par = u_current_idw[depth]
                            elif parameters[0] == 'u_comp_cur_':
                                band_par = v_current_idw[depth]
                        elif fore_area == 'ws':
                            depth = int(self.depth_box_ws.currentText())
                            if parameters[0] == 'salinity_':
                                band_par = salinity_ws[depth]
                            elif parameters[0] == 'water_temp_':
                                band_par = water_temp_ws[depth]
                            elif parameters[0] == 'v_comp_cur_':
                                band_par = u_current_ws[depth]
                            elif parameters[0] == 'u_comp_cur_':
                                band_par = v_current_ws[depth]
                        elif fore_area == 'if':
                            depth = int(self.depth_box_if.currentText())
                            if parameters[0] == 'salinity_':
                                band_par = salinity_if[depth]
                            elif parameters[0] == 'water_temp_':
                                band_par = water_temp_if[depth]
                            elif parameters[0] == 'v_comp_cur_':
                                band_par = u_current_if[depth]
                            elif parameters[0] == 'u_comp_cur_':
                                band_par = v_current_if[depth]
                        elif fore_area == 'lf':
                            depth = int(self.depth_box_lf.currentText())
                            if parameters[0] == 'salinity_':
                                band_par = salinity_lf[depth]
                            elif parameters[0] == 'water_temp_':
                                band_par = water_temp_lf[depth]
                            elif parameters[0] == 'v_comp_cur_':
                                band_par = u_current_lf[depth]
                            elif parameters[0] == 'u_comp_cur_':
                                band_par = v_current_lf[depth]
                        elif fore_area == 'lb':
                            depth = int(self.depth_box_lb.currentText())
                            if parameters[0] == 'salinity_':
                                band_par = salinity_lb[depth]
                            elif parameters[0] == 'water_temp_':
                                band_par = water_temp_lb[depth]
                            elif parameters[0] == 'v_comp_cur_':
                                band_par = u_current_lb[depth]
                            elif parameters[0] == 'u_comp_cur_':
                                band_par = v_current_lb[depth]
                    elif parameters[0] not in depth_para_dkss:
                        band_par = para_fore_dict_nsbs[parameters[0]]
                # Provides the statistics for the layer. Used to find min and max
                stats = layer.dataProvider().bandStatistics(band_par, QgsRasterBandStats.All)
                # The layer will be mapped in a Gray symbology
                renderer = QgsSingleBandGrayRenderer(layer.dataProvider(), band_par)
                # Sets the color scale for the layer
                myType = renderer.dataType(1)
                myEnhancement = QgsContrastEnhancement(myType)
                contrast_enhancement = QgsContrastEnhancement.StretchToMinimumMaximum
                myEnhancement.setContrastEnhancementAlgorithm(contrast_enhancement, True)
                myEnhancement.setMinimumValue(stats.minimumValue)
                myEnhancement.setMaximumValue(stats.maximumValue)
                d = feature['properties']['datetime']
                start_time = QDateTime.fromString(d, 'yyyy-MM-ddThh:mm:ssZ')
                end_time = start_time.addSecs(3600)
                time_range = QgsDateTimeRange(start_time, end_time)
                layer.temporalProperties().setFixedTemporalRange(time_range)
                layer.temporalProperties().setIsActive(True)
                layer.setRenderer(renderer)
                layer.renderer().setContrastEnhancement(myEnhancement)


                # Changes the name
                if len(parameters) > 0:
                    if self.wam_fore.isChecked():
                        layer.setName(data_type2 + ' ' + fore_area + ' ' + parameters[0] + ' ' + feature['properties']['datetime'])
                    elif self.dkss_fore.isChecked() and parameters[0] in depth_para_dkss:
                        layer.setName(data_type2 + ' ' + fore_area + ' ' + parameters[0] + ' ' + str(depth) + 'm ' + feature['properties']['datetime'])
                    elif self.dkss_fore.isChecked() and parameters[0] not in depth_para_dkss:
                        layer.setName(data_type2 + ' ' + fore_area + ' ' + parameters[0] + ' ' + feature['properties']['datetime'])
                elif len(parameters) == 0:
                    layer.setName(data_type2 + ' ' + fore_area + ' ' + 'All parameters ' + feature['properties']['datetime'])
                # Adds the layer to the map
                project = QgsProject.instance()
                project.addMapLayer(layer, addToLegend=False)
                layer_group.insertLayer(-1, layer)
        # Information about stations and parameters
        if dataName == 'Stations and Parameters':
            if self.met_stat_info.isChecked():
                data_type = 'climateData'
                api_key = self.settings_manager.value(DMISettingKeys.CLIMATEDATA_API_KEY.value)
                data_type2 = 'station'
            elif self.tide_info.isChecked():
                data_type = 'oceanObs'
                api_key = self.settings_manager.value(DMISettingKeys.OCEANOBS_API_KEY.value)
                data_type2 = 'station'
            url = 'https://dmigw.govcloud.dk/v2/' + data_type + '/collections/' + data_type2 +'/items'
            params = {'api-key': api_key}
            # metObs info
            if self.met_stat_info.isChecked():
                if self.radioButton_11.isChecked() and self.radioButton.isChecked():
                    params.update({'datetime': datetime,
                              'status': 'Active'})
                elif self.radioButton_10.isChecked() and self.radioButton_9.isChecked():
                    params = params
                elif self.radioButton.isChecked() and self.radioButton_10.isChecked():
                    params.update({'status': 'Active'})
                elif self.radioButton_9.isChecked() and self.radioButton_11.isChecked():
                    params.update({'datetime': datetime})
            # ocean info
            if self.tide_info.isChecked():
                if self.radioButton_20.isChecked() and self.radioButton_22.isChecked():
                    params.update({'datetime': datetime,
                              'status': 'Active'})
                elif self.radioButton_19.isChecked() and self.radioButton_21.isChecked():
                    params = params
                elif self.radioButton_20.isChecked() and self.radioButton_21.isChecked():
                    params.update({'status': 'Active'})
                elif self.radioButton_19.isChecked() and self.radioButton_22.isChecked():
                    params.update({'datetime': datetime})
            r = requests.get(url, params=params)
            print(r.url)
            json = r.json()
            r_code = r.status_code
            if r_code == 403:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                 self.tr('API Key is not valid or is expired / revoked.'))
            else:
                df = json_normalize(json['features'])
                # Name and sort the data based on users preferences
                if self.met_stat_info.isChecked():
                    if self.radioButton_2.isChecked():
                        df = df.loc[df['properties.country'] == 'DNK']
                        name_stations_met = 'Meteorological Stations Denmark'
                    elif self.radioButton_3.isChecked():
                        df = df.loc[df['properties.country'] == 'GRL']
                        name_stations_met = 'Meteorological Stations Greenland'
                    elif self.radioButton_4.isChecked():
                        name_stations_met = 'All Meteorological Stations'
                if self.tide_info.isChecked():
                    if self.radioButton_14.isChecked():
                        name_stations_met = 'All stations'
                    elif self.radioButton_12.isChecked():
                        df = df.loc[df['properties.owner'] == 'DMI']
                        name_stations_met = 'DMI'
                    elif self.radioButton_13.isChecked():
                        df = df.loc[df['properties.owner'] == 'Kystdirektoratet / Coastal Authority']
                        name_stations_met = 'Coastal Authority'
                # Names the layer as the station type and parameter if parameter is chosen.
                if len(parameters) != 0:
                    df = df[pd.DataFrame(df['properties.parameterId'].tolist()).isin(parameters).any(1).values]
                    name_stations_met = name_stations_met + ' ' + parameters[0]
                if len(df) == 0:
                    QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('No stations meets this requirement.'))
                elif len(df) > 0:
                    # QGIS geometry
                    vl = QgsVectorLayer("Point", name_stations_met, "memory")
                    for row in df.itertuples():
                        pr = vl.dataProvider()
                        vl.startEditing()
                        for head in df:
                            if head != 'geometry.coordinates':
                                pr.addAttributes([QgsField(head, QVariant.String)])
                        vl.updateFields()
                        f = QgsFeature()
                        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(row[3][0], row[3][1])))
                        if data_type == 'climateData':
                            f.setAttributes([row[1],row[2],row[4],row[5],row[6],row[7],\
                                                row[8],row[9],row[10],row[11],str(row[12]),row[13],row[14],\
                                                row[15],row[16],row[17],row[18],row[19],row[20],row[21],row[22]])
                        elif data_type == 'oceanObs':
                            f.setAttributes([row[1], row[2], row[4], row[5], row[6], str(row[7]), \
                                             row[8], row[9], row[10], row[11], str(row[12]), row[13], row[14], \
                                             row[15], row[16], row[17], row[18], row[19], row[20], row[21]])
                        vl.addFeature(f)
                        vl.updateExtents()
                    vl.commitChanges()
                    QgsProject.instance().addMapLayer(vl)
                iface.zoomToActiveLayer()
        if len(error_stats) != 0:
            QMessageBox.warning(self, self.tr("DMI Open Data"),
                                self.tr('Following stations does not produce all the desired data.' + '\n' + 'Change parameters, time and/or resolution.' + '\n' + '\n' + '\n'.join(set(error_stats))))
