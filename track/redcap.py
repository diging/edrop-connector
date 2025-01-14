import requests
from django.conf import settings
import logging
from http import HTTPStatus

logger = logging.getLogger(__name__)

def get_record_info(record_id):
    # TODO: put field names in settings
    data = {
        'token': settings.REDCAP_TOKEN,
        'content': 'record',
        'action': 'export',
        'format': 'json',
        'type': 'flat',
        'csvDelimiter': '',
        'records[0]': record_id,
        'fields[0]': 'record_id',
        'fields[1]': 'first_name',
        'fields[2]': 'last_name',
        'fields[3]': 'city',
        'fields[4]': 'state',
        'fields[5]': 'zip',
        'fields[6]': 'street',
        'rawOrLabel': 'raw',
        'rawOrLabelHeaders': 'raw',
        'exportCheckboxLabel': 'false',
        'exportSurveyFields': 'false',
        'exportDataAccessGroups': 'false',
        'returnFormat': 'json'
    }
    r = requests.post(settings.REDCAP_URL,data=data)
    logger.error('REDCap HTTP Status: ' + str(r.status_code))

    if r.status_code == HTTPStatus.OK:
        return r.json()
    
    # TODO: throw exception and handle
    return None
