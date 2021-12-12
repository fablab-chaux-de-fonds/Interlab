from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sessions.models import Session
from django.http import HttpResponse    
from django.template import loader
from django.utils.translation import ugettext as _
from django.shortcuts import redirect, render

from .forms import EditProfileForm
from .forms import CustomOrganizationUserAddForm
from .models import Profile

from organizations.models import OrganizationUser
from organizations.views.base import BaseOrganizationUserCreate
from organizations.views.mixins import OwnerRequiredMixin


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

@login_required
def DeleteOrganizationUserView(request, organization_pk, user_pk):
    template = "organizations/organizationuser_confirm_delete.html"
    organization_user = OrganizationUser.objects.get(user_id=user_pk, organization_id=organization_pk)
    context ={
        "organization_user": organization_user
    }

    if request.method == 'POST':

        organization_user.delete()

        try:
            profile = Profile.objects.get(user_id=user_pk)
            profile.subscription = None
            profile.save()
        except Profile.DoesNotExist:
            pass

        if organization_user.user.first_name:
            messages.success(request, organization_user.user.first_name + organization_user.user.last_name + _(" has been removed succesffully from the team.") )
        else:
            messages.success(request, organization_user.user.email + _(" has been removed successfully from the team.") )
        return redirect('organization_detail', organization_pk=request.user.organizations_organization.first().pk)
    
    return render(request, template, context)


class OrganizationUserCreateView(OwnerRequiredMixin, LoginRequiredMixin, BaseOrganizationUserCreate):
    form_class = CustomOrganizationUserAddForm

