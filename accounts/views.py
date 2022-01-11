from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sessions.models import Session
from django.http import HttpResponse    
from django.template import loader
from django.utils.translation import ugettext as _
from django.shortcuts import redirect, render

from .models import Profile, SubscriptionCategory
from .forms import EditProfileForm, CustomOrganizationUserAddForm, CustomRegistrationForm

from organizations.views.base import BaseOrganizationUserCreate
from organizations.views.base import BaseOrganizationUserDelete
from organizations.views.mixins import OwnerRequiredMixin

from django_registration.backends.activation.views import RegistrationView
from django_registration import signals

from newsletter.views import register_email

class CustomRegistrationView(RegistrationView):
    template_name = 'registration/registration_form.html'
    form_class = CustomRegistrationForm

    def register(self, form):
        new_user = self.create_inactive_user(form)

        # Add user to newsletter list
        if form.cleaned_data['newsletter']: 
            register_email(form.cleaned_data['email'])
        
        signals.user_registered.send(
            sender=self.__class__, user=new_user, request=self.request
        )
        return new_user

@login_required
def AccountsView(request):
    user = request.user
    template = loader.get_template('accounts/profile.html')
    context = {
        'page_title': "My account",
        'organization': request.user.organizations_organization.first(),
        'user': user
    }

    subscription = Profile.objects.get(user_id=user.id).subscription
    if subscription is not None:
        context['subscription'] = subscription
        context['subscription_category']=SubscriptionCategory.objects.get(pk=subscription.subscription_category_id)
        
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

class OrganizationUserDeleteView(OwnerRequiredMixin, LoginRequiredMixin, BaseOrganizationUserDelete):
    def post(self, request, *args, **kwargs):

        # Remove user from organization
        self.organization.remove_user(self.organization_user.user)

        # Remove subscription of the user
        try:
            profile = Profile.objects.get(user_id=self.organization_user.user_id)
            profile.subscription = None
            profile.save()
        except Profile.DoesNotExist:
            pass
        
        if self.organization_user.user.first_name:
            messages.success(request, self.organization_user.user.first_name + self.organization_user.user.last_name + _(" has been removed succesffully from the team.") )
        else:
            messages.success(request, self.organization_user.user.email + _(" has been removed successfully from the team.") )
        return redirect('organization_detail', organization_pk=request.user.organizations_organization.first().pk)

class OrganizationUserCreateView(OwnerRequiredMixin, LoginRequiredMixin, BaseOrganizationUserCreate):
    form_class = CustomOrganizationUserAddForm

def token_error_view(request): 
    template = 'organizations/invitations_token_error.html'
    return render(request, template) 
