import requests
from django.conf import settings
import logging
from http import HTTPStatus
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

def get_record_info(record_id):
    """
    Get information from a REDCap record to receive shipping address. Requests the
    following fields from REDCap:
    - 'record_id',
    - 'first_name',
    - 'last_name',
    - 'city',
    - 'state',
    - 'zip',
    - 'street',
    - 'consent_complete'

    Returns a dictionary, which contains the address information, e.g.:
    {
        'record_id': '1', 
        'redcap_repeat_instrument': '', 
        'redcap_repeat_instance': '', 
        'first_name': 'Scissors', 
        'last_name': 'Paper', 
        'street': 'Paper', 
        'city': 'Paper', 
        'state': 'KS', 
        'zip': '55112', 
        'consent_complete': '2'
    }
    """
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
        'fields[7]': 'consent_complete',
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
        records = r.json()
        # Since we are requested only one record, REDCap will return a list of dictionaries,
        # with only one dictionary.
        if records:
            return records[0]
    
    # TODO: throw exception and handle
    return None

def set_order_number(record_id, order_number):

    xml = f"""
    <?xml version="1.0" encoding="UTF-8" ?>
    <records>
    <item>
        <record_id>{record_id}</record_id>
        <kit_order_n>{order_number}</kit_order_n>
    </item>
    </records>
    """
    
    data = {
        'token': settings.REDCAP_TOKEN,
        'content': 'record',
        'action': 'import',
        'format': 'xml',
        'type': 'flat',
        'overwriteBehavior': 'normal',
        'forceAutoNumber': 'false',
        'data': xml,
        'returnContent': 'count',
        'returnFormat': 'json'
    }
    r = requests.post(settings.REDCAP_URL, data=data)
    
    if r.status_code != HTTPStatus.OK:
        logger.error('HTTP Status: ' + str(r.status_code))
        logger.error(r.json())
    else:
        logger.debug("Succesfully send order number to REDCap.")

def set_tracking_info(order_objects):
    root = ET.Element("records")

    for order in order_objects:
        item = ET.SubElement("item")
        ET.SubElement(item, "record_id").text = order.record_id
        ET.SubElement(item, "date_kit_shipped").text = order.ship_date
        ET.SubElement(item, "kit_tracking_n").text = order.tracking_nr
        #ET.SubElement(item, RETURN TRACKING).text = ?

    xml = ET.tostring(root, encoding="unicode")
    
    data = {
        'token': settings.REDCAP_TOKEN,
        'content': 'record',
        'action': 'import',
        'format': 'xml',
        'type': 'flat',
        'overwriteBehavior': 'normal',
        'forceAutoNumber': 'false',
        'data': xml,
        'returnContent': 'count',
        'returnFormat': 'json'
    }
    r = requests.post(settings.REDCAP_URL, data=data)
    
    if r.status_code != HTTPStatus.OK:
        logger.error('HTTP Status: ' + str(r.status_code))
        logger.error(r.json())
    else:
        logger.debug("Succesfully sent tracking information to REDCap.")