import requests
from django.conf import settings
import logging, inspect
from http import HTTPStatus
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz

from track.models import *
from track.log_manager import LogManager
from track.exceptions import REDCapError

logger = logging.getLogger(__name__)
log_manager = LogManager()


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
    - 'street_1',
    - 'street_2',
    - consent_complete
    - 'contact_complete'

    Returns a dictionary, which contains the address information, e.g.:
    {
        'record_id': '1', 
        'redcap_repeat_instrument': '', 
        'redcap_repeat_instance': '', 
        'first_name': 'Scissors', 
        'last_name': 'Paper', 
        'street_1': 'Paper', 
        'street_2': 'Rock', 
        'city': 'Paper', 
        'state': 'KS', 
        'zip': '55112', 
        'consent_complete': '2',
        'contact_complete': '2'
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
    logger.debug(f'REDCap HTTP Status: {str(r.status_code)}')

    if r.status_code == HTTPStatus.OK:
        records = r.json()
        # Since we are requested only one record, REDCap will return a list of dictionaries,
        # with only one dictionary.
        if records:
            return records[0]
    else:
        logger.error("Could not get record data from REDCap.")
        logger.error(f'REDCap HTTP Status: {str(r.status_code)}')
        raise REDCapError(f"REDCap returned {r.status_code}.")
    
    return None

def set_order_number(record_id, order_number):
    """ 
    This method will save the given order number to the REDCap record with 
    the provided record id. It also sets the kit_tracking_complete to one to indicate
    that the order is in progress.
    """

    xml = f"""
    <?xml version="1.0" encoding="UTF-8" ?>
    <records>
    <item>
        <record_id>{record_id}</record_id>
        <kit_order_n>{order_number}</kit_order_n>
        <date_kit_request>{datetime.now(pytz.timezone(settings.REQUEST_TIMEZONE)).strftime("%Y-%m-%d")}</date_kit_request>
        <kit_status>ORD</kit_status>
        <kit_tracking_complete>1</kit_tracking_complete>
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
        logger.error(f'HTTP Status: {r.status_code}')
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
            <kit_tracking_complete>1</kit_tracking_complete>
            <kit_tracking_return_n>inbound tracking</kit_tracking_return_n>
            <tubeserial>tube serial1</tubeserial>
        </item>
    </records>
    """
    root = ET.Element("records")

    # we only care about the orders that have a ship date
    order_objects = list(filter(lambda order: order.ship_date, order_objects))

    if not order_objects:
        message = "No confirmations received. Nothing to send to REDCap."
        log_manager.append_to_redcap_log(LogManager.LEVEL_INFO, message)
        logger.info(message)
        return

    for order in order_objects:

        # in case an order has not been shipped yet, we don't update REDcap
        if not order.ship_date:
            continue
              
        item = ET.SubElement(root, "item")
        ET.SubElement(item, "record_id").text = order.record_id
        ET.SubElement(item, "date_kit_shipped").text = order.ship_date
        ET.SubElement(item, "kit_tracking_n").text = ", ".join(order.tracking_nrs)
        # we make sure that the tracking complete field is set to 1 (Unverified)
        ET.SubElement(item, "kit_tracking_complete").text = "1"
        # we set the kitstatus to "In Transit"
        ET.SubElement(item, "kit_status").text = "TRN"
        ET.SubElement(item, "kit_tracking_return_n").text = ", ".join(order.return_tracking_nrs)
        ET.SubElement(item, "tubeserial").text = ", ".join(order.tube_serials)

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
        message = f'HTTP Status: {str(r.status_code)}'
        log_manager.append_to_redcap_log(LogManager.LEVEL_ERROR, message)
        logger.error(message)

        message = r.json()
        log_manager.append_to_redcap_log(LogManager.LEVEL_ERROR, message)
        logger.error(message)
    else:
        message = f"Succesfully sent tracking information to REDCap for the following records: {[order.record_id for order in order_objects]}."
        log_manager.append_to_redcap_log(LogManager.LEVEL_INFO, message)
        logger.info(message)
        
    log_manager.complete_log()