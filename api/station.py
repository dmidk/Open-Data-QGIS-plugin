from itertools import groupby
from typing import Tuple, Dict, List

import requests
from enum import Enum

StationId = str
StationName = str


class StationApi(Enum):
    class _Inner:
        base_url_path: str
        def __init__(self, base_url_path: str):
            self.base_url_path = base_url_path

    MET_OBS = _Inner('v2/metObs')
    OCEAN_OBS = _Inner('v2/oceanObs')
    CLIMATE_STATION_VALUE = _Inner('v2/climateData')


class Station:
    station_id: str
    station_name: str
    parameters: List[str]

    def __init__(self, station_id, station_name, parameters):
        self.station_id = station_id
        self.station_name = station_name
        self.parameters = parameters


def get_stations(station_api: StationApi, api_key: str) -> Dict[StationId, Station]:
    """
    Generates station ids and corresponding names, picking current name for active stations, and latest used name for
    inactive ones
    :param station_api: ObsApi enum of which API should be used
    :param api_key: API key for calls to the API
    :return: dictionary of station id and name
    """
    station_params = {'api-key': api_key}
    obs_station_request = requests.get(
        f'https://dmigw.govcloud.dk/{station_api.value.base_url_path}/collections/station/items',
        params=station_params
    )
    json = obs_station_request.json()
    station_map = {}
    for station_id, stations in groupby(json['features'], key=lambda station: station['properties']['stationId']):
        # Choose the latest station record to pick station name from
        latest_station = sorted(stations, key=lambda station: station['properties']['validFrom'])[-1]
        station_map[station_id] = Station(station_id, latest_station['properties']['name'], latest_station['properties']['parameterId'])
    return station_map
