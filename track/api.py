from django.http import JsonResponse, HttpResponse
from http import HTTPStatus
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from track.models import *
import track.orders as orders

import logging
logger = logging.getLogger(__name__)

@csrf_exempt
def initiate_order(request):
    if request.method != 'POST':
        return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)
    
    # if instrument is not "consent", we don't care 
    if request.POST.get('instrument', '').strip() != settings.REDCAP_INSTRUMENT_ID:
        logger.debug("Instrument is not contact.")
        return HttpResponse(status=HTTPStatus.OK)
    
    # and contact_complete is not 2, we don't care
    if request.POST.get(settings.REDCAP_FIELD_TO_BE_COMPLETE) != '2':
        logger.debug("Contact is not complete.")
        return HttpResponse(status=HTTPStatus.OK)
    
    record_id = request.POST.get('record')
    order = Order.objects.filter(record_id=record_id).first()
    if order and order.order_number and order.order_status != Order.PENDING:
        # order has already been placed, so do nothing
        logger.debug("An order has already been placed.")
        return HttpResponse(status=HTTPStatus.OK)
    
    # create a new order only if no order exists
    order = orders.place_order(record_id, request.POST.get('project_id'), request.POST.get('project_url'))
    if not order:
        logger.error("Endpoint was called with contact_complete = 2 but REDCap order actually does not have contact_complete = 2.")
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)

    logger.debug(f"Order initiated for record {request.POST.get('record', None)}")
    
    return JsonResponse({'status':'ok'})
 