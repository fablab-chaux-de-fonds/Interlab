import smtplib
from datetime import datetime
from crispy_forms.helper import FormHelper

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Q 
from django.forms import ModelForm
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from phonenumber_field.formfields import PhoneNumberField

from organizations.forms import OrganizationUserAddForm
from organizations.backends import invitation_backend

from django_registration.forms import RegistrationForm
from .models import SubscriptionCategory, Subscription, Profile, CustomUser

from machines.models import Training, TrainingValidation

class EditUserForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        del self.fields['password']

    class Meta:
        model = CustomUser
        labels = {
        'email': _("email")
        }
        fields = ('first_name','last_name','username','email')

class EditProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ('phone_number','public_contact_plateform','public_contact')
        widgets = {
           'phone_number': forms.TextInput(attrs={ 'class': 'form-control' }),
           'public_contact_plateform': forms.Select(attrs={ 'class': 'form-control' }),
           'public_contact': forms.TextInput(attrs={ 'class': 'form-control' })
       }


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label=_('Email / Username'))
    password= forms.PasswordInput(attrs={'data-toggle': 'password'})

    def clean(self):
        # TODO - clean with super() method !
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)

            ############################################
            # Check if user active before check password
            # https://github.com/django/django/blob/main/django/contrib/auth/forms.py
            User = get_user_model()
            try: 
                user = User.objects.get( Q(username=username) | Q(email=username) )
            except User.DoesNotExist:
                raise self.get_invalid_login_error()

            if not user.is_active and self.user_cache is None:
                raise ValidationError(
                    _("You have not yet validated your e-mail. Please click on the activation link that we sent you by email when you created your account.")
            )
            ############################################

            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
        
class CustomOrganizationUserAddForm(OrganizationUserAddForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        if self.organization.users.filter(email__iexact=email).exists():
            raise ValidationError(
                _("There is already an organization member with this email address!")
            )
        if get_user_model().objects.filter(email__iexact=email).count() > 1:
            raise ValidationError(
                _("This email address has been used multiple times.")
            )
        
        # Check domain
        try: 
            user = invitation_backend().invite_by_email(
                self.cleaned_data["email"],
                **{
                    "domain": get_current_site(self.request),
                    "organization": self.organization,
                    "sender": self.request.user,
                }
            )
        except smtplib.SMTPRecipientsRefused:
            raise ValidationError(
                _("Recipient address rejected: Domain not found")
            )

        return email

class CustomRegistrationForm(RegistrationForm):
    "This form is used for registration - Base class form Django"
    first_name = forms.CharField(max_length=50, label=_('First name')) # Required
    last_name = forms.CharField(max_length=50, label=_('Last name')) # Required
    newsletter = forms.BooleanField(required=False, label=_('I subscribe to the newsletter'), help_text=_('about once a month'))
    class Meta(RegistrationForm.Meta):
            model = get_user_model()
            help_texts  = {
                'username' : _('150 characters maximum. Only letters, numbers and the characters "@", ".", "+", "-" and "_".')
            }
            fields = ['first_name','last_name','username','email','password1','password2', 'newsletter']

class CustomUserRegistrationForm(CustomRegistrationForm):
    "This form is used when the user in invited with django-organization"
    email = forms.EmailField(widget=forms.TextInput(
        attrs={'class': 'disabled', 'readonly': 'readonly'}))

class SuperuserProfileEditForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False 

    subscription_category = forms.ModelChoiceField(
        queryset=SubscriptionCategory.objects.all(),
        empty_label=_('No Subscription'),
        required=False)

    start = forms.CharField()
    end = forms.CharField()
    
    training = forms.ModelMultipleChoiceField(
        queryset=Training.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
        )

    def _remove_subscription(self, view, user_profile: Profile):
        user_profile.subscription = None
        user_profile.save()
        messages.success(view.request, mark_safe(_('Remove subscription for user {}'.format(user_profile.user))))

    def _create_subscription(self, view, new_subscription_category: int, user_profile: Profile):
        # Only send mail for new subscriptions
        is_new_subscription = user_profile.subscription is None
        
        # Default value start today
        today = datetime.today()
        
        user_profile.subscription = Subscription.objects.create(
            subscription_category = new_subscription_category,
            access_number = new_subscription_category.default_access_number,
            start = self.start or today,
            end = self.end or (today + new_subscription_category.duration)
        )
        # When subscription is defined, it means it has changed somehow, save it.
        user_profile.subscription.save()
        user_profile.save()

        # Notify super-user of operation result
        messages.success(
            view.request, 
            mark_safe(_("Subcription updated to %(subcription_category)s for user %(user)s") % {
                'subcription_category': user_profile.subscription.subscription_category.title if user_profile.subscription is not None else '',
                'user': str(user_profile.user)
            })
        )

        # --- New subscription email sending ---
        if is_new_subscription:
            self._send_subscription_mail(view)


    def _update_duration(self, view, user_profile: Profile):
        user_profile.subscription.start = self.start
        user_profile.subscription.end = self.end
        user_profile.subscription.save()
        messages.success(view.request, mark_safe(_('Subscription duration updated for user {}'.format(user_profile.user))))

    def update_or_create_subscription(self, view):
        (user_profile, is_new_profile) = Profile.objects.get_or_create(user=view.user)
        
        old_subscription_category_pk = None
        if user_profile.subscription is not None \
            and user_profile.subscription.subscription_category is not None:
            old_subscription_category_pk = user_profile.subscription.subscription_category.pk

        new_subscription_category = self.cleaned_data.get('subscription_category', None)
        new_subscription_category_pk = new_subscription_category.pk if new_subscription_category is not None else None

        if new_subscription_category_pk != old_subscription_category_pk:
            if new_subscription_category is None:
                self._remove_subscription(view, user_profile)
            else:
                self._create_subscription(view, new_subscription_category, user_profile)
        elif user_profile.subscription is not None \
            and (self.initial.get('start', self.start) != self.start or self.initial.get('end', self.end) != self.end):
                self._update_duration(view, user_profile)
        elif is_new_profile:
            user_profile.save()

    def _send_subscription_mail(self, view):
        view.context['profile'] = Profile.objects.get(user=view.user)
        html_message = render_to_string('accounts/email/new_subscription.html', view.context)

        send_mail(
            from_email=None,
            subject=_("Welcome to Fablab !"),
            message = _("A new training was planned"),
            recipient_list = [view.user.email],
            html_message = html_message
        )

    def update_training_validation(self, view):

        if not 'training' in self.initial:
            self.initial['training']=[]
        
        selectedTrainings = self.cleaned_data.get('training', None)
        if selectedTrainings is None:
            return
        
        userTrainings = TrainingValidation.objects.filter(profile=view.user.profile)

        # Deleting trainings not in new selection
        for trainingValidation in userTrainings.exclude(training__pk__in=selectedTrainings):
            trainingValidation.delete()

            messages.success(view.request, 
                _("Training %(training)s has been successfully deleted for %(first_name)s %(last_name)s") % {'training': trainingValidation.training.title, 'first_name': view.user.first_name, 'last_name': view.user.last_name}
            )

            view.context = {'training': trainingValidation.training}
            html_message = render_to_string('accounts/email/delete_training_validation.html', view.context)

            send_mail(
                from_email=None,
                subject=_("Sorry, we cancel your training validation"),
                message = _("Training deleted"),
                recipient_list = [view.user.email],
                html_message = html_message
            )  


        existingTrainings = [t.training.pk for t in userTrainings]
        for trainingValidation in Training.objects.exclude(pk__in=existingTrainings).filter(pk__in=selectedTrainings):
            TrainingValidation.objects.create(
                profile = view.user.profile,
                training = trainingValidation
            )

            messages.success(view.request, 
                _("Training %(training)s has been successfully valided for %(first_name)s %(last_name)s") % {'training': trainingValidation.title, 'first_name': view.user.first_name, 'last_name': view.user.last_name}
            )

            view.context = {'training': trainingValidation}

            html_message = render_to_string('accounts/email/create_training_validation.html', view.context)

            send_mail(
                from_email=None,
                subject=_("Start to use the machine !"),
                message = _("Training validated"),
                recipient_list = [view.user.email],
                html_message = html_message
            )