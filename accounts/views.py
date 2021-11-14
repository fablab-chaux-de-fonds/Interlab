from django.http import HttpResponse    
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import ugettext as _

from .models import Profile, SubscriptionCategory
from .forms import EditProfileForm

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

@login_required
def EditProfileView(request):
    template = 'accounts/profile_edit.html'
    context = {
        'page_title': "Edit my profile" 
    }

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your profile has been updated successfully") )
            return redirect(AccountsView)

    else:
        form = EditProfileForm(instance=request.user)

    context["edit_profile_form"] = form

    print(context)

    return render(request, template, context)