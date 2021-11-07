from django.http import HttpResponse    
from django.template import loader
from django.contrib.auth.decorators import login_required

from .models import Accounts

@login_required
def AccountsView(request):
    template = loader.get_template('accounts/profile.html')
    context = {
        'page_title': "My accounts",
        'user': request.user
    }
    return HttpResponse(template.render(context, request))