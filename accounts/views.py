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
from django.db.models import Q, OuterRef, Subquery, Exists, Value
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic.base import TemplateView


from fabcal.models import EventSlot, OpeningSlot, TrainingSlot, MachineSlot, RegistrationEventSlot
from machines.models import TrainingValidation

from .forms import EditUserForm, EditProfileForm, CustomOrganizationUserAddForm, CustomRegistrationForm, CustomAuthenticationForm, SuperuserProfileEditForm
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

@login_required
def AccountsView(request):
    user = request.user
    template = loader.get_template('accounts/profile.html')

    today = datetime.date.today()

    # Subquery to check if the user has registrations for the event slot
    registration_event_slot = RegistrationEventSlot.objects.filter(
        event_slot=OuterRef('pk'),
        event_slot__end__gte=today,
        user=request.user
    )

    context = {
        'page_title': "My account",
        'user': user,
        'slots': sorted(chain(
            TrainingSlot.objects.filter(user=request.user, end__gte=datetime.date.today()),
            TrainingSlot.objects.filter(registrations=request.user, end__gte=datetime.date.today()),
            EventSlot.objects.filter(user=request.user, end__gte=datetime.date.today()),
            EventSlot.objects.filter(Exists(registration_event_slot)),
            OpeningSlot.objects.filter(user=request.user, end__gte=datetime.date.today()), 
            MachineSlot.objects.filter(user=request.user, end__gte=datetime.date.today()),
        ),
        key=attrgetter('start')
        )
    }

    (profile, _) = Profile.objects.get_or_create(user=user)
    if profile.subscription is not None:
        context['subscription'] = profile.subscription
        context['subscription_category']=profile.subscription.subscription_category_id
        
    return HttpResponse(template.render(context, request))

@login_required
def EditProfileView(request):
    template = 'accounts/profile_edit.html'

    if request.method == 'POST':
        user_form = EditUserForm(request.POST, instance=request.user)
        profile_form = EditProfileForm(request.POST, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            # Check if profile has newsletter
            contacts = get_contact()
            mail_list = [contact['email'] for contact in contacts['data']['data']]
            if 'email' in user_form.changed_data:
                old_email = user_form.initial['email']
                if old_email in mail_list:
                    user_id = next((contact['id'] for contact in contacts['data']['data'] if contact['email'] == old_email), None)
                    if user_id is not None:
                        new_email = user_form.cleaned_data['email']
                        update_contact(user_id, new_email)
                        messages.success(request, _("Your newsletter registration has been updated successfully with the email address: ") + new_email)

            user_form.save()
            profile_form.save()

            messages.success(request, _("Your profile has been updated successfully"))
            return redirect(AccountsView)
    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = EditProfileForm(instance=request.user.profile)

    context = {
        "edit_user_form": user_form,
        "edit_profile_form": profile_form
    }

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
        return reverse('accounts:user-list')

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
