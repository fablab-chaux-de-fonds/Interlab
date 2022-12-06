import datetime
from itertools import chain
from operator import attrgetter
import dateparser

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Q 
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader
from django.utils.encoding import force_str
from django.utils.translation import ugettext as _
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic.base import TemplateView

from fabcal.models import EventSlot, OpeningSlot, TrainingSlot, MachineSlot
from machines.models import TrainingValidation

from .forms import EditProfileForm, CustomOrganizationUserAddForm, CustomRegistrationForm, CustomAuthenticationForm, SuperuserProfileEditForm
from .models import Profile, SubscriptionCategory

from organizations.views.base import BaseOrganizationUserCreate
from organizations.views.base import BaseOrganizationUserDelete
from organizations.views.mixins import OwnerRequiredMixin

from django_registration.backends.activation.views import RegistrationView, ActivationView
from django_registration import signals
from django_registration.exceptions import ActivationError

from newsletter.views import register_email, get_contact, update_contact
from interlab.views import CustomFormView
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
    user = request.user
    template = loader.get_template('accounts/profile.html')
    context = {
        'page_title': "My account",
        'user': user,
        'slots': sorted(chain(
            TrainingSlot.objects.filter(user=request.user, end__gt=datetime.datetime.now()),
            OpeningSlot.objects.filter(user=request.user, end__gt=datetime.datetime.now()), 
            MachineSlot.objects.filter(user=request.user, end__gt=datetime.datetime.now())
        ),
        key=attrgetter('start')
        )
    }
    try:
        subscription = Profile.objects.get(user_id=user.id).subscription
    except ObjectDoesNotExist:
        profile = Profile(user=request.user, subscription=None)
        profile.save()

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


class UserListView(LoginRequiredMixin, TemplateView):
    number_of_item = 10

    def get(self, *args, **kwargs):
        if not self.request.user.groups.filter(name = 'superuser').exists():
            raise PermissionDenied
        else:
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

class SuperuserProfileEditView(LoginRequiredMixin, CustomFormView):
    template_name = 'accounts/superuser-profile-edit.html'
    form_class = SuperuserProfileEditForm

    def get_success_url(self):
        return reverse('user-list')

    def get_initial(self):
        initial = super().get_initial()
        self.user = get_user_model().objects.get(pk=self.kwargs['pk'])
        if self.user.profile is not None \
            and self.user.profile.subscription is not None \
            and self.user.profile.subscription.subscription_category is not None:
            initial['subscription_category'] = self.user.profile.subscription.subscription_category
            initial['start'] = self.user.profile.subscription.start
            initial['end'] = self.user.profile.subscription.end

        if self.user.profile is not None:
             initial['training'] = [t.training.pk for t in TrainingValidation.objects.filter(profile=self.user.profile)]

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.user

        if context['form'].initial.get('subscription_category', None) is not None:
            context['start'] = context['form'].initial['start']
            context['end'] = context['form'].initial['end']
        else:
            today = datetime.datetime.today()
            context['start'] = today
            context['end'] = today + datetime.timedelta(days=365)
        return context
    
    def form_invalide(self):
        pass

    def form_valid(self, form):
        if 'subscription_category' in form.changed_data or \
            'start' in form.changed_data or \
            'end' in form.changed_data:

            if 'start' in form.cleaned_data:
                form.start = dateparser.parse(form.cleaned_data['start']).date()
            
            if 'end' in form.cleaned_data:
                form.end = dateparser.parse(form.cleaned_data['end']).date()

            if form.start is not None and form.end is not None and form.start >= form.end:
                messages.error(self.request, _('Invalid subscription duration from %(start)s to %(end)s') % {'start':form.start, 'end':form.end})
                return super().form_valid(form)

            self.context={'user': self.user}
            form.update_or_create_subscription(self)

        if 'training' in form.changed_data:
            form.update_training_validation(self)
        
        return super().form_valid(form)
