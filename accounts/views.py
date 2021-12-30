from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.sessions.models import Session
from django.core.paginator import Paginator
from django.db.models import Q 
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader
from django.utils.encoding import force_str
from django.utils.translation import ugettext as _
from django.shortcuts import redirect, render
from django.views.generic.base import TemplateView

from .forms import EditProfileForm, CustomOrganizationUserAddForm, CustomRegistrationForm, CustomAuthenticationForm
from .models import Profile, Subscription, SubscriptionCategory

from organizations.views.base import BaseOrganizationUserCreate
from organizations.views.base import BaseOrganizationUserDelete
from organizations.views.mixins import OwnerRequiredMixin

from django_registration.backends.activation.views import RegistrationView, ActivationView
from django_registration import signals
from django_registration.exceptions import ActivationError

from newsletter.views import register_email, get_contact, update_contact
class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
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

class CustomActivationView(ActivationView):
    
    def get(self, *args, **kwargs):
        """
        The base activation logic; subclasses should leave this method
        alone and implement activate(), which is called from this
        method.
        """
        extra_context = {}
        try:
            activated_user = self.activate(*args, **kwargs)
        except ActivationError as e:
            
            ###################################
            #Check if account already activated
            #https://github.com/ubernostrum/django-registration/blob/3.2/src/django_registration/views.py
            if e.code == 'already_activated':
                self.template_name = "django_registration/already_activated.html"
            ###################################

            extra_context["activation_error"] = {
                "message": e.message,
                "code": e.code,
                "params": e.params,
            }
        else:
            signals.user_activated.send(
                sender=self.__class__, user=activated_user, request=self.request
            )
            return HttpResponseRedirect(force_str(self.get_success_url(activated_user)))
        context_data = self.get_context_data()
        context_data.update(extra_context)
        return self.render_to_response(context_data)

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

            # Check if profile has newsletter
            contacts = get_contact()
            mail_list = [ x['email'] for x in contacts['data']['data']]
            if 'email' in form.changed_data and form.initial['email'] in mail_list:
                user_id = [x['id'] for x in contacts['data']['data'] if x['email'] == form.initial['email']][0]
                update_contact(user_id, form.cleaned_data['email'])
                messages.success(request, _("Your newsletter registration has been updated successfully with the email address: ") + form.cleaned_data['email'])

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


class UserListView(TemplateView):
    number_of_item = 10

    def get(self, *args, **kwargs):
        template = self.template_name
        context = self.get_context_data()
        return render(self.request, template, context)

    def post(self, *args, **kwargs):
        template = self.template_name
        context = self.get_context_data()
        return render(self.request, template, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = self.find_user(self.request.POST.get('search'))
        users = self.get_page_obj(self.request, users, self.number_of_item)
        context['users'] = users
        return context

    def get_page_obj(self, request, list_of_objects, number_of_item):
        paginator = Paginator(list_of_objects, number_of_item)
        page_number = request.GET.get('page')
        return paginator.get_page(page_number)

    def find_user(self, query):
        qs = get_user_model().objects.all()
        if query:
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

    try:
        initial = {'subscription_category': user.profile.subscription.subscription_category.pk}
    except AttributeError: 
        initial = {'subscription_category': 'no-subscription'}

    if request.method == 'POST':
        subcription_form = UserSubcriptionForm(request.POST)
        if subcription_form.is_valid():
            if str(initial['subscription_category']) != subcription_form.cleaned_data['subscription_category']:
                if subcription_form.cleaned_data['subscription_category'] == 'no-subscription':
                    s = None
                    message = _("Subscription deleted successfully for user ") 
                    if user.first_name:
                        message += user.first_name + ' ' + user.last_name
                    else:
                        message += user.email
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
                    message = _("Subcription updated to %(subcription_category)s for user ") % {'subcription_category': subcription_category.title}
                    if user.first_name:
                       message += user.first_name + ' ' + user.last_name
                    else:
                        message += user.email + user.first_name + ' ' + user.last_name 
                
                Profile.objects.update_or_create(user=user, defaults={'subscription':s})
                messages.success(request, message)

            return redirect('user-list')
    else:
        subcription_form = UserSubcriptionForm(initial)
        context = {
            'subcription_form': subcription_form, 
            'user': user
        }
    return render(request, template, context)