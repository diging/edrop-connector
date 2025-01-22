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
        'fields[6]': 'street_1',
        'fields[7]': 'street_2',
        'fields[8]': 'consent_complete',
        'fields[9]': 'contact_complete',
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
    logger.error(r.json())
    return None

def set_order_number(record_id, order_number):

    xml = f"""
    <?xml version="1.0" encoding="UTF-8" ?>
    <records>
    <item>
        <record_id>{record_id}</record_id>
        <kit_order_n>{order_number}</kit_order_n>
        <kit_status>ORD</kit_status>
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
        logger.error('redcap.set_order_number: HTTP Status: ' + str(r.status_code))
        logger.error(r.json())
    else:
        logger.debug("Succesfully send order number to REDCap.")

def set_tracking_info(order_objects):
    """
    Method to save the shipping and tracking info for shipped orders in REDCap. 
    This method builds XML that looks like this:

    <records>
        <item>
            <record_id>2</record_id>
            <date_kit_shipped>2023-01-12</date_kit_shipped>
            <kit_tracking_n>outbound tracking 1, outbound tracking 2</kit_tracking_n>
            <kit_status>TRN</kit_status>
        </item>
    </records>
    """
    root = ET.Element("records")
    
    for order in order_objects:

        # in case an order has not been shipped yet, we don't update REDcap
        if not order.ship_date:
            continue
              
        item = ET.SubElement(root, "item")
        ET.SubElement(item, "record_id").text = order.record_id
        ET.SubElement(item, "date_kit_shipped").text = order.ship_date
        ET.SubElement(item, "kit_tracking_n").text = ", ".join(order.tracking_nrs)
        # we set the kitstatus to "In Transit"
        ET.SubElement(item, "kit_status").text = "TRN"
        #TODO: Handle return_tracking_nr property
        #ET.SubElement(item, RETURN TRACKING).text = ?

    xml = ET.tostring(root, encoding="unicode")
    logger.error(xml)

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
        logger.error('orders.set_tracking_info: HTTP Status: ' + str(r.status_code))
        logger.error(r.json())
    else:
        logger.error("Succesfully sent tracking information to REDCap.")