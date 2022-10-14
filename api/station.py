from datetime import datetime
from itertools import groupby
from typing import Dict, List, Iterable
from functools import lru_cache
from PyQt5.QtCore import QVariant
from qgis.core import QgsFeature, QgsFields, QgsField, QgsGeometry, QgsPointXY
import requests
from enum import Enum
from operator import attrgetter
from ..util import rfc3339_zulu_format

StationId = str
StationName = str
Parameter = str


def get_qvariant(python_type):
    if python_type == str:
        return QVariant.String
    if python_type == float:
        return QVariant.Double
    if python_type == int:
        return QVariant.Int
    if python_type == datetime:
        return QVariant.DateTime


class StationApi(Enum):
    class _Inner:
        base_url_path: str
        def __init__(self, base_url_path: str):
            self.base_url_path = base_url_path

    MET_OBS = _Inner('v2/metObs')
    OCEAN_OBS = _Inner('v2/oceanObs')
    CLIMATE_STATION_VALUE = _Inner('v2/climateData')

    def get_api_name(self) -> str:
        if self is StationApi.MET_OBS:
            return 'MetObs API'
        if self is StationApi.OCEAN_OBS:
            return 'OceanObs API'
        if self is StationApi.CLIMATE_STATION_VALUE:
            return 'Climate Data API'


class StationStatus(Enum):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'


class StationOwner(Enum):
    DMI = 'DMI'
    KDI = 'Kystdirektoratet / Coastal Authority'


class StationCountry(Enum):
    DENMARK = 'DNK'
    GREENLAND = 'GRL'


class Station:
    latitude: float
    longitude: float
    station_id: str
    station_name: str
    parameters: List[Parameter]
    barometer_height: float
    country: str
    created: datetime
    operation_from: datetime
    operation_to: datetime
    owner: str
    region_id: str
    station_height: float
    status: str
    station_type: str
    updated: str
    valid_from: datetime
    valid_to: datetime
    wmo_country_code: str
    wmo_station_id: str

    def __init__(self, geojson_feature):
        self.longitude = geojson_feature['geometry']['coordinates'][0]
        self.latitude = geojson_feature['geometry']['coordinates'][1]
        self.station_id = geojson_feature['properties']['stationId']
        self.station_name = geojson_feature['properties']['name']
        self.parameters = geojson_feature['properties']['parameterId']
        # Some stations (like oceanObs stations) does not have barometer height, therefore this attribute is optional
        if barometer_height := geojson_feature['properties'].get('barometerHeight'):
            self.barometer_height = barometer_height
        self.country = geojson_feature['properties']['country']
        self.created = datetime.strptime(geojson_feature['properties']['created'], rfc3339_zulu_format)
        if operation_from := geojson_feature['properties']['operationFrom']:
            self.operation_from = datetime.strptime(operation_from, rfc3339_zulu_format)
        if operation_to := geojson_feature['properties']['operationTo']:
            self.operation_to = datetime.strptime(operation_to, rfc3339_zulu_format)
        self.owner = geojson_feature['properties']['owner']
        self.region_id = geojson_feature['properties']['regionId']
        if station_height := geojson_feature['properties'].get('stationHeight'):
            self.station_height = station_height
        self.status = geojson_feature['properties']['status']
        self.station_type = geojson_feature['properties']['type']
        self.updated = geojson_feature['properties']['updated']
        self.valid_from = datetime.strptime(geojson_feature['properties']['validFrom'], rfc3339_zulu_format)
        if valid_to := geojson_feature['properties']['validTo']:
            self.valid_to = datetime.strptime(valid_to, rfc3339_zulu_format)
        self.wmo_country_code = geojson_feature['properties']['wmoCountryCode']
        self.wmo_station_id = geojson_feature['properties']['wmoStationId']

    def as_qgs_feature(self) -> QgsFeature:
        qgs_feature = QgsFeature()
        qgs_feature.setFields(Station.qgs_fields())
        qgs_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(self.longitude, self.latitude)))
        for attr, value in [(attr, value) for attr, value in vars(self).items() if attr not in ['longitude', 'latitude', 'parameters']]:
            # While QGIS accepts QVariant.Datetime as QgsField type (even though the documentation says otherwise) the
            # value of the field still has to be a string. With ISO formatting the temporal features of QGIS works when
            # the field type is QVariant.Datetime
            if type(value) == datetime:
                value = value.isoformat()
            qgs_feature.setAttribute(attr, value)
        return qgs_feature

    @classmethod
    @lru_cache(maxsize=None)
    def qgs_fields(cls) -> QgsFields:
        qgs_fields = QgsFields()
        for property_name, python_type in [(p, t) for p, t in cls.__annotations__.items() if p not in ['latitude', 'longitude', 'parameters']]:
            qgs_fields.append(QgsField(property_name, get_qvariant(python_type)))
        return qgs_fields


class StationAPIGenericException(Exception):
    def __init__(self):
        super().__init__("API request failed, try again or check for network issues")


class StationAPIAuthException(Exception):
    def __init__(self, station_api: StationApi):
        super().__init__(f"API Key for {station_api.get_api_name()} is not valid or is expired / revoked.")


def _station_api_call(station_api: StationApi, api_key: str, status: StationStatus = None,
                      start_datetime: datetime = None, end_datetime: datetime = None, station_type: str = None) -> Iterable[Station]:
    station_params = {'api-key': api_key}
    if status:
        station_params['status'] = status.value
    if start_datetime or end_datetime:
        datetime_param = ''
        if start_datetime:
            datetime_param += start_datetime.strftime(rfc3339_zulu_format)
        else:
            datetime_param += '..'
        datetime_param += '/'
        if end_datetime:
            datetime_param += end_datetime.strftime(rfc3339_zulu_format)
        else:
            datetime_param += '..'
        station_params['datetime'] = datetime_param
    if station_type:
        station_params['type'] = station_type
    try:
        obs_station_request = requests.get(
            f'https://dmigw.govcloud.dk/{station_api.value.base_url_path}/collections/station/items',
            params=station_params
        )
    except Exception:
        raise StationAPIGenericException()

    if obs_station_request.status_code == 403:
        raise StationAPIAuthException(station_api)
    elif obs_station_request.status_code != 200:
        raise StationAPIGenericException()

    json = obs_station_request.json()
    return map(lambda station_json_feature: Station(station_json_feature), json['features'])


def get_folded_stations(station_api: StationApi, api_key: str) -> Dict[StationId, Station]:
    """
    Generates station ids and corresponding names, picking current name for active stations, and latest used name for
    inactive ones
    :param station_api: ObsApi enum of which API should be used
    :param api_key: API key for calls to the API
    :return: dictionary of station id and name
    """
    stations = _station_api_call(station_api, api_key)
    station_map = {}
    stations = sorted(stations, key=attrgetter('station_id'))  # pre-sort for groupby to work correctly
    for station_id, station_group in groupby(stations, key=attrgetter('station_id')):
        # Choose the latest station record to pick station name from
        latest_station = sorted(station_group, key=attrgetter('valid_from'))[-1]
        station_map[station_id] = latest_station
    return station_map


def get_stations(station_api: StationApi, api_key: str, status=None, start_datetime: datetime = None,
                 end_datetime: datetime = None, country: StationCountry = None, owner: StationOwner = None,
                 station_type: str = None,
                 parameters: List[str] = None) -> Iterable[Station]:
    stations = _station_api_call(station_api, api_key, status=status, start_datetime=start_datetime,
                                 end_datetime=end_datetime, station_type=station_type)
    if country:
        stations = filter(lambda station: station.country == country.value, stations)
    if owner:
        stations = filter(lambda station: station.owner == owner.value, stations)
    if parameters:
        stations = filter(lambda station: any(parameter in station.parameters for parameter in parameters), stations)
    return stations
