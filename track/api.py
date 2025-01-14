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
    if request.POST.get('instrument', '').strip() != settings.REDCAP_CONSENT_INSTRUMENT_ID:
        logger.debug("Instrument is not consent.")
        return HttpResponse(status=HTTPStatus.OK)
    
    # and concent_complete is not 2, we don't care
    if request.POST.get('consent_complete') != '2':
        logger.debug("Consent is not complete.")
        return HttpResponse(status=HTTPStatus.OK)
    
    record_id = request.POST.get('record')
    existing_order = Order.objects.filter(record_id=record_id).first()
    if existing_order and existing_order.order_number and existing_order.order_status != Order.PENDING:
        # order has already been placed, so do nothing
        logger.debug("An order has already been placed.")
        return HttpResponse(status=HTTPStatus.OK)
    
    # TODO: do not create duplicate orders
    new_order = orders.create_order(record_id, request.POST.get('project_id'), request.POST.get('project_url'))

    # TODO: post order number back to redcap
    logger.error(f"Order initiated {request.POST.get('record', None)}")
    logger.error(request.POST)
    
    return JsonResponse({'status':'ok'})
 