# -*- coding: utf-8 -*-
import os
from typing import Tuple, Dict, Set

from qgis.PyQt import QtWidgets, uic
import requests
import pandas as pd
from pandas.io.json import json_normalize
import warnings
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsContrastEnhancement, QgsRasterMinMaxOrigin, QgsFeature, QgsGeometry, QgsField, QgsPointXY, QgsProject, QgsRasterLayerTemporalProperties, QgsDateTimeRange
from qgis.utils import iface
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from qgis.PyQt.QtCore import QVariant
import webbrowser

from .dmi_dialog_tabs.information import DMIInformationWidget
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

        # Initializing information widget
        information_widget = DMIInformationWidget(self.settings_manager, parent=self.information_tab)
        layout = self.information_tab.findChildren(QtWidgets.QVBoxLayout)[0]
        layout.addWidget(information_widget)

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

        # Datetime default today and yesterday
        self.start_date.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.end_date.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.climate_data_start_date_dateedit.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.climate_data_end_date_dateedit.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.radar_start_date.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.radar_end_date.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

        self.lightning_start_date.setDateTime(QDateTime(QDate.currentDate().addDays(-1), QTime(0, 0, 0)))
        self.lightning_end_date.setDateTime(QDateTime(QDate.currentDate(), QTime(0, 0, 0)))

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
        self.stackedWidget.setCurrentWidget(self.stat_clima)
        self.stackedWidget_2.setCurrentWidget(self.stat_para)
        self.stackedWidget_3.setCurrentWidget(self.met_stat_page)
        self.met_stat_info.clicked.connect(self.infoStat)
        self.tide_info.clicked.connect(self.infoTide)
        self.radioButton_10.clicked.connect(self.disable_time)
        self.radioButton_11.clicked.connect(self.enable_time)
        self.radioButton_21.clicked.connect(self.disable_time_oce)
        self.radioButton_22.clicked.connect(self.enable_time_oce)
        self.dmi_open_data_2.clicked.connect(self.open_openData_2)
        # Sets the time in "Stations and parameters" unavailable untill "Defined Time" has been checked
        self.groupBox_25.setEnabled(False)
        self.groupBox_26.setEnabled(False)
        self.dateTimeEdit_3.setEnabled(False)
        self.dateTimeEdit_4.setEnabled(False)

        self.radar_disable_if_needed()
        self.lightning_disable_if_needed()

    def radar_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.RADARDATA_API_KEY.value)
        if api_key == '':
            layout = self.tab_3.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.RADARDATA_API_KEY))
            self.radar_start_date.setEnabled(False)
            self.radar_end_date.setEnabled(False)

    def lightning_disable_if_needed(self):
        api_key = self.settings_manager.value(DMISettingKeys.LIGHTNINGDATA_API_KEY.value)
        if api_key == '':
            layout = self.lightning_tab.findChildren(QtWidgets.QVBoxLayout)[0]
            layout.addWidget(DMIOpenDataDialog.generate_no_api_key_label(DMISettingKeys.LIGHTNINGDATA_API_KEY))
            self.bbox_lightning.setEnabled(False)
            self.all_lightning_types.setEnabled(False)
            self.cloud_to_g_pos.setEnabled(False)
            self.cloud_to_g_neg.setEnabled(False)
            self.cloud_to_cloud.setEnabled(False)
            self.lightning_start_date.setEnabled(False)
            self.lightning_end_date.setEnabled(False)

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
# Actions for buttons to go to dmi.dk
    def open_openData_2(self):
        webbrowser.open('https://confluence.govcloud.dk/display/FDAPI/Danish+Meteorological+Institute+-+Open+Data')
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
            api_key = self.api_forecastData.text()
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
            data_type2 = 'composite'
        elif data_type == 'forecastdata':
            data_type2 = 'forecast'
        elif data_type == '':
            data_type2 = ''
        elif data_type == 'stat_para_info':
            data_type2 = 'climateData'
        elif data_type == 'ocean_para_info':
            data_type2 = 'oceanObs'

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

# Datetime
# Changes the format of the datetime to make it compatible for the URL calls.
# The format by QT is yyyy:m:d h:m:s and the format needed for URL is yyyy:mm:ddThh:mm:ssZ
        if dataName == 'Meteorological Observations':
            start_datetime = self.start_date.dateTime().toString(Qt.ISODate) + 'Z'
            end_datetime = self.end_date.dateTime().toString(Qt.ISODate) + 'Z'


            #start_year = self.start_date.date().year()
            #start_month = self.start_date.date().month()
            #start_day = self.start_date.date().day()
            #start_hour = self.start_date.time().hour()
            #start_minute = self.start_date.time().minute()
            #start_second = self.start_date.time().second()

            #end_year = self.end_date.date().year()
            #end_month = self.end_date.date().month()
            #end_day = self.end_date.date().day()
            #end_hour = self.end_date.time().hour()
            #end_minute = self.end_date.time().minute()
            #end_second = self.end_date.time().second()
            
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

        #elif dataName == 'Forecast Data':
            #start_datetime = self.start_date2.dateTime().toString(Qt.ISODate)
            #end_datetime = self.end_date2.dateTime().toString(Qt.ISODate)

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

# URL creation for metObs and cliamteData
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
# When 0 is assigned to num, it means that the program shouldnt run further, as there is an issue with data.
# num is only used in climateData, metObs and oceanObs.
        if dataName == 'Climate Data' or dataName == 'Meteorological Observations' or dataName == 'Oceanographic Observations':
            if len(stations) == 0:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('Please select a station.'))
                num = 0
            if len(parameters) == 0:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('Please select a parameter.'))
                num = 0
# Iterates over each station that has been checked by the user.
# It is only possible to check stations in climateData, metObs and oceanObs. This section is therefor only for these 3.
        for stat in stations:
            url = 'https://dmigw.govcloud.dk/v2/' + data_type + '/collections/' + data_type2 + '/items'
# Two dataframes are created to sort the data.
# The second is created further down.
            df1 = pd.DataFrame()
# Iterates over all the parameters that has been checked by the user.
            for para in parameters:
# Only Climate Data has resolution.
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
                    num = 0
                    QMessageBox.warning(self, self.tr("DMI Open Data"), self.tr('API Key is not valid or is expired / revoked.'))
# if the call has the right API, then continue. This does not mean that the call will deliver data!
# The station could still not be measuring the wished parameter.
                elif r_code != 403:
                    num = json['numberReturned']
                if num > 0:
# A pandas DataFrame is created to easier manage the data, and to convert to csv.
# All parameters will be appended to the dataframe created earlier, and the header will change name to the parameter.
                    df = json_normalize(json['features'])
                    df1[para] = df['properties.value'].tolist()
# If the API is correct but the chosen parameter is not measured by the station.
                elif num == 0 and r_code != 403:
                    if dataName == 'Climate Data':
                        QMessageBox.warning(self, self.tr("DMI Open Data"), self.tr(para + ' is not available for ' + stat + \
                                                                                    '. Change resolution, parameter or time.'))
                    elif dataName == 'Meteorological Observations' or dataName == 'Oceanographic Observations':
                        QMessageBox.warning(self, self.tr("DMI Open Data"),
                                                self.tr(para + ' is not available for ' + stat + \
                                                        '. Change parameter or time.'))
# It is only possible to choose 7 parameters.
                elif len(parameters) > 7:
                    num = 0
                    QMessageBox.warning(self, self.tr("DMI Open Data"),
                                        self.tr('Maximum amount of parameters allowed is 7. Please change amount of parameters.'))
                    parameters.remove(para)
# If num > 0 then the program will stop.
            if num > 0:
# Changes the name of the header and adds it to the new dataframe
                if data_type2 == 'observation':
                    df['properties.observed'] = pd.to_datetime(df['properties.observed'])
                    df1['observed'] = df['properties.observed'].dt.strftime('%Y-%m-%d %H:%M')
                elif data_type == 'climateData':
                    df['properties.from'] = pd.to_datetime(df['properties.from'])
                    df1['from'] = df['properties.from'].dt.strftime('%Y-%m-%d %H:%M')
                    df1['to'] = df['properties.to']
                if stat1 == 'stationId':
                    df1[stat1] = df['properties.stationId']
                elif stat1 == 'cellId':
                    df1[stat1] = df['properties.cellId']
                elif stat1 == 'municipalityId':
                    df1[stat1] = df['properties.municipalityId']
# QGIS geometry
# The coordinate for the station
                koordinater = df['geometry.coordinates'].iloc[0]
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
                for head in df1:
                    if head == 'observed':
                        pr.addAttributes([QgsField(head, QVariant.DateTime)])
                    elif head != 'observed':
                        pr.addAttributes([QgsField(head, QVariant.String)])
                vl.updateFields()
                f = QgsFeature()
# Iterates over the rows in the df. This depends on the amount of parameters called.
# Maximum numbers of parameters available is 7 because of this.
# Cliamte data has 2 datetimes where metObs only has 1 which explains the following if statement.
                if dataName == 'Climate Data' and data_type2 != 'countryValue':
                    for row in df1.itertuples():
                        if len(parameters) == 1:
                            listee = [row[1],row[2],row[3],row[4]]
                        elif len(parameters) == 2:
                            listee = [row[1],row[2],row[3],row[4],row[5]]
                        elif len(parameters) == 3:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6]]
                        elif len(parameters) == 4:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6],row[7]]
                        elif len(parameters) == 5:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8]]
                        elif len(parameters) == 6:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9]]
                        elif len(parameters) == 7:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]]
                        f.setAttributes(listee)
                        vl.addFeature(f)
                elif data_type2 == 'observation' or data_type2 == 'countryValue':
                    for row in df1.itertuples():
                        if len(parameters) == 1:
                            listee = [row[1],row[2],row[3]]
                        elif len(parameters) == 2:
                            listee = [row[1],row[2],row[3],row[4]]
                        elif len(parameters) == 3:
                            listee = [row[1],row[2],row[3],row[4],row[5]]
                        elif len(parameters) == 4:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6]]
                        elif len(parameters) == 5:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6],row[7]]
                        elif len(parameters) == 6:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8]]
                        elif len(parameters) == 7:
                            listee = [row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9]]
                        f.setAttributes(listee)
                        vl.addFeature(f)
# The coordinates are used based on which type of geometry (polygon or point).
                if stat1 == 'stationId' or stat1 == 'municipalityId' or data_type2 == 'countryValue':
                    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(koordinater[0],koordinater[1])))
                    vl.addFeature(f)
                    vl.updateExtents()
                    vl.commitChanges()
                elif stat1 == 'cellId':
                    koordi = [QgsPointXY(koordinater[0][0][0],koordinater[0][0][1]),QgsPointXY(koordinater[0][1][0],koordinater[0][1][1]),\
                              QgsPointXY(koordinater[0][2][0],koordinater[0][2][1]),QgsPointXY(koordinater[0][3][0],koordinater[0][3][1]),\
                              QgsPointXY(koordinater[0][4][0],koordinater[0][4][1])]
                    f.setGeometry(QgsGeometry.fromPolygonXY([koordi]))
                    vl.addFeature(f)
                    vl.updateExtents()
                    vl.commitChanges()
                QgsProject.instance().addMapLayer(vl)
# The files are saved, if the user has chosen to write something in the "save as .csv" section
        if dataName == 'Meteorological Observations':
            if self.file_name_obs.text() == '':
                pass
            else:
                df1.to_csv(self.file_name_obs.text() + '.csv', index=False)
                self.file_name_obs.clear()
        elif dataName == 'Climate Data':
            if self.file_name_cli.text() == '':
                pass
            else:
                df1.to_csv(self.file_name_cli.text() + '.csv', index=False)
                self.file_name_cli.clear()
        elif dataName == 'Oceanographic Observations':
            if self.file_name_oce.text() == '':
                pass
            else:
                df1.to_csv(self.file_name_oce.text() + '.csv', index=False)
                self.file_name_oce.clear()
# URL call radar data
        if dataName == 'Radar Data':
            root = QgsProject.instance().layerTreeRoot()
            layer_group = root.insertGroup(0, 'Radar' + datetime)
            temp = "temp-folder"
            url = 'https://dmigw.govcloud.dk/v1/' + data_type + '/collections/' + data_type2 + '/items'
            params = {'api-key' : api_key,
                    'datetime' : datetime,
                      'limit': 300000}
            r = requests.get(url, params=params)
            print(r.url)
            r_code = r.status_code
            json = r.json()
            if r_code == 403:
                num = 0
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('API Key is not valid or is expired / revoked.'))
            elif r_code != 403:
                num = json['numberReturned']
            if num == 0:
                QMessageBox.warning(self, self.tr("DMI Open Data"), self.tr('Radar data is only available 6 months prior to current date, and has a delay in upload. \
                Please change date and time.'))
            elif num > 0:
                for feature in json['features']:
                    downloadurl = feature['asset']['data']['href']
                    downloaddata = requests.get(downloadurl)
                    id = feature['id']
                    if "0.500" not in id:
                        continue
                    tempfile = temp + id
                    if not os.path.isfile(tempfile):
                        with open(tempfile, 'wb') as fd:
                            for chunk in downloaddata.iter_content(chunk_size=128):
                                fd.write(chunk)
                    layer = QgsRasterLayer(tempfile)
                    layer.setName(id)

                    # Set layer tempral properties to be from image date to + 10 minutes
                    layer.temporalProperties().setMode(QgsRasterLayerTemporalProperties.ModeFixedTemporalRange)
                    d = feature['properties']['datetime']
                    start_time = QDateTime.fromString(d, "yyyy-MM-ddThh:mm:ssZ")
                    end_time = start_time.addSecs(600)
                    time_range = QgsDateTimeRange(start_time, end_time)
                    layer.temporalProperties().setFixedTemporalRange(time_range)
                    layer.temporalProperties().setIsActive(True)
# This removes all values below 1 and above 254, since this only consists of white and black fields.
                    layer.setContrastEnhancement(algorithm=QgsContrastEnhancement.ClipToMinimumMaximum,
                                                     limits=QgsRasterMinMaxOrigin.MinMax)
                    layer.renderer().contrastEnhancement().setMinimumValue(1)
                    layer.renderer().contrastEnhancement().setMaximumValue(254)
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
                num = 0
            elif r_code != 403:
                num = json['numberReturned']
                df = json_normalize(json['features'])
            if num == 0 and r_code != 403:
                QMessageBox.warning(self, self.tr("DMI Open Data"),
                                    self.tr('No lightnings observed. Change time or parameter.'))
            elif num > 0:
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
            temp = "TODO" # TODO
            url = 'https://dmigw.govcloud.dk/v1/forecastdata/collections/wam_dw/items'
            params = {'api-key' : api_key,
                    'limit' : '1'}
            r = requests.get(url, params=params)
            print(r, r.url)
            json = r.json()
            for feature in json['features']:
                downloadurl = feature['asset']['data']['href']
                downloaddata = requests.get(downloadurl)
                id = feature['id']
                print(id)
                if "0.500" not in id:
                    continue
                tempfile = temp + id
                if not os.path.isfile(tempfile):
                    with open(tempfile, 'wb') as fd:
                        for chunk in downloaddata.iter_content():
                            fd.write(chunk)
                layer = QgsRasterLayer(tempfile)
                layer.setName(id)
                project = QgsProject.instance()
                project.addMapLayer(layer)

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
