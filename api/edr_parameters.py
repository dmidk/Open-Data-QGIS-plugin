from typing import Tuple, Dict, List

import requests
from enum import Enum

ParameterId = str
ParameterDescription = str
ParameterInfo = Tuple[ParameterId, ParameterDescription]

class EDRForecastCollection(Enum):
    collection: str

    HARMONIE_NEA_SF = 'harmonie_nea_sf'
    HARMONIE_NEA_PL = 'harmonie_nea_pl'
    HARMONIE_IGB_SF = 'harmonie_igb_sf'
    HARMONIE_IGB_PL = 'harmonie_igb_pl'
    DKSS_NSBS = 'dkss_nsbs'
    DKSS_IDW = 'dkss_idw'
    DKSS_IF = 'dkss_if'
    DKSS_WS = 'dkss_ws'
    DKSS_LF = 'dkss_lf'
    DKSS_LB = 'dkss_lb'
    WAM_DW = 'wam_dw'
    WAM_NSB = 'wam_nsb'
    WAM_NATLANT = 'wam_natlant'

def get_forecast_parameters(forecast_collection: EDRForecastCollection, api_key: str) -> List[ParameterInfo]:
    edr_params = {'api-key': api_key}
    forecast_para_request = requests.get(
        f'https://dmigw.govcloud.dk/v1/forecastedr/collections/{forecast_collection.value}',
        params=edr_params
    )
    forecast_metadata = forecast_para_request.json()
    parameters = []
    for parameter_id, parameter_metadata in forecast_metadata['parameter_names'].items():
        parameters.append((parameter_id, parameter_metadata['description']))
    return parameters
