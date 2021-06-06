from django.http import HttpResponse
from django.template import loader

def bootstrap(request):
    template = loader.get_template('bootstrap.html')
    context = {}
    return HttpResponse(template.render(context, request))