from django import template
from django.http import HttpResponse    
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.utils.translation import ugettext as _

from .forms import EditProfileForm

@login_required
def AccountsView(request):
    template = loader.get_template('accounts/profile.html')
    context = {
        'page_title': "My account",
        'organization': request.user.organizations_organization.first()
    }
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

    return render(request, template, context)

@login_required
def DeleteProfileView(request):
    template = 'accounts/profile_delete.html'
    context = {
        'page_title': "Delete my profile" 
    }
    if request.method == 'POST':
        user = request.user
        user.is_active = False
        user.save()
        messages.success(request, _("Your account has been successfully deleted") )
        [s.delete() for s in Session.objects.all() if s.get_decoded().get('_auth_user_id') == user.id]
        return redirect('/')

    return render(request, template, context)