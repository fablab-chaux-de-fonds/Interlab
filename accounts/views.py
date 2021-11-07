from django.http import HttpResponse    
from django.template import loader
from django.contrib.auth.decorators import login_required

from .models import Profile, SubscriptionCategory

@login_required
def AccountsView(request):
    user = request.user
    subscription = Profile.objects.get(user_id=user.id).subscription

    template = loader.get_template('accounts/profile.html')
    context = {
        'page_title': "My account",
        'user': user,
        'subscription': subscription,    
    }

    if subscription:
       context['subscription_category']=SubscriptionCategory.objects.get(pk=subscription.category_id)

    return HttpResponse(template.render(context, request))