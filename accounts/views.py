from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import update_last_login
from django.contrib.sessions.models import Session
from django.db.models import Q 
from django.http import HttpResponse    
from django.template import loader
from django.utils.translation import ugettext as _
from django.shortcuts import redirect, render

from .forms import EditProfileForm
from .forms import CustomOrganizationUserAddForm, CustomRegistrationForm
from .models import Profile, Subscription, SubscriptionCategory

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
    template = loader.get_template('accounts/profile.html')
    context = {
        'page_title': "My account",
        'organization': request.user.organizations_organization.first(),
        'user' : request.user
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
            messages.success(request, self.organization_user.user.first_name + self.organization_user.user.last_name + _(" has been removed successfully from the team.") )
        else:
            messages.success(request, self.organization_user.user.email + _(" has been removed successfully from the team.") )
        return redirect('organization_detail', organization_pk=request.user.organizations_organization.first().pk)

class OrganizationUserCreateView(OwnerRequiredMixin, LoginRequiredMixin, BaseOrganizationUserCreate):
    form_class = CustomOrganizationUserAddForm

def token_error_view(request): 
    template = 'organizations/invitations_token_error.html'
    return render(request, template) 

def user_list(request): 
    template = 'accounts/user-list.html'
    User = get_user_model()
    users = User.objects.all()

    context = {
        'users': users
    }
    return render(request, template, context)

def user_list_filtered(request):
    template = 'accounts/user-list-filtered.html'

    context = {
        'users': find_user(request.POST.get('search'))
    }
    return render(request, template, context)

def find_user(query):
    qs = get_user_model().objects.all()
    for term in query.split():
        qs = qs.filter( 
            Q(first_name__icontains = term) | 
            Q(last_name__icontains = term) |
            Q(email__icontains = term)
            )
    return qs

from .forms import UserSubcriptionForm
import datetime

def user_edit(request, user_pk):
    template = 'accounts/user-edit.html'
    User = get_user_model()
    user = User.objects.get(pk=user_pk)

    if request.method == 'POST':
        subcription_form = UserSubcriptionForm(request.POST)
        if subcription_form.is_valid():
            if 'subscription_category' in subcription_form.changed_data:
                if subcription_form.cleaned_data['subscription_category'] == 'no-subscription':
                   s = None
                   message = _("Subscription deleted successfully for user ") + user.first_name + ' ' + user.last_name
                else: 
                    subcription_category = SubscriptionCategory.objects.get(pk=subcription_form.cleaned_data['subscription_category'])
                    kwargs = {
                            "start" : datetime.datetime.now(),
                            "end" : datetime.datetime.now() + datetime.timedelta(days=subcription_category.duration),
                            "subscription_category" : subcription_category,
                            "access_number" : subcription_category.default_access_number
                    }

                    s = Subscription(**kwargs)
                    s.save()
                    message = _("Subcription updated to ") + subcription_category.title + _(' for user ') + user.first_name + ' ' + user.last_name 
                
                Profile.objects.update_or_create(user=user, defaults={'subscription':s})
                messages.success(request, message)

                return redirect('user-list')
                
    elif request.method == "GET":
        try:
            initial = {'subscription_category': user.profile.subscription.subscription_category.pk}
        except AttributeError: 
            initial = {'subscription_category': 'no-subscription'}

        subcription_form = UserSubcriptionForm(initial)

        context = {
            'subcription_form': subcription_form, 
            'user': user
        }
    
    return render(request, template, context)