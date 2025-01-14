from django.http import JsonResponse, HttpResponse
from http import HTTPStatus
from django.views.decorators.csrf import csrf_exempt

import logging
logger = logging.getLogger(__name__)

@csrf_exempt
def initiate_order(request):
    
    if request.method != 'POST':
        return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)
    
    # TODO: initiate order shipment
    logger.error(f"Order initiated {request.POST.get('record', None)}")
    logger.error(request.POST)
    
    return JsonResponse({'status':'ok'})
 