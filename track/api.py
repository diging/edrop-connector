from django.http import JsonResponse, HttpResponse
from http import HTTPStatus
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def initiate_order(request):
    
    if request.method != 'POST':
        return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)
    
    # TODO: initiate order shipment
    print(f"Order initiated {request.GET.get('record', None)}")
    
    return JsonResponse({'status':'ok'})
 