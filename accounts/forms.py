import smtplib
from crispy_forms.helper import FormHelper

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Q 
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from organizations.forms import OrganizationUserAddForm
from organizations.backends import invitation_backend

from django_registration.forms import RegistrationForm
from .models import SubscriptionCategory, Subscription, Profile

from machines.models import Training, TrainingValidation

class EditProfileForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        del self.fields['password']

    class Meta:
        model = User
        labels = {
        'email': _("email")
        }
        fields = ('first_name','last_name','username','email',)

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label=_('Email / Username'))
    password= forms.PasswordInput(attrs={'data-toggle': 'password'})

    def clean(self):
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

    def update_or_create_subscription(self, view):

        subcription_category = self.cleaned_data['subscription_category']
        kwargs = {
                'subscription_category': subcription_category,
                'start': self.start,
                'end': self.end,
                "access_number" : subcription_category.default_access_number
        }
        s = Subscription(**kwargs)
        s.save()

        Profile.objects.update_or_create(user=view.user, defaults={'subscription':s})

        message = _("Subcription updated to %(subcription_category)s for user ") % {'subcription_category': subcription_category.title}
       
        if view.user.first_name:
            message += view.user.first_name + ' ' + view.user.last_name
        else:
            message += view.user.email + view.user.first_name + ' ' + view.user.last_name 

        messages.success(view.request, mark_safe(message))
    
    def send_subscription_mail(self, view):
        html_message = render_to_string('accounts/email/new_subscription.html', view.context)

        send_mail(
            from_email=None,
            subject=_("Welcome to Fablab !"),
            message = _("A new training was planned"),
            recipient_list = [view.user.email],
            html_message = html_message
        )

    def update_training_validation(self, view):
        
        # check if new training selected and created it
        for training in self.cleaned_data['training']:
            if not training.pk in self.initial['training']:
                TrainingValidation.objects.create(
                    profile = view.user.profile,
                    training = training
                )

                messages.success(view.request, 
                    _("Training %(training)s has been successfully valided for %(first_name)s %(last_name)s") % {'training': training.title, 'first_name': view.user.first_name, 'last_name': view.user.last_name}
                )

                view.context = {'training': training}

                html_message = render_to_string('accounts/email/create_training_validation.html', view.context)

                send_mail(
                    from_email=None,
                    subject=_("Start to use the machine !"),
                    message = _("Training validated"),
                    recipient_list = [view.user.email],
                    html_message = html_message
                )
       
        # check if a training has been unchecked and delete it
        for pk in self.initial['training']:
            if not pk in [training.pk for training in self.cleaned_data['training']]:
                training = Training.objects.get(pk=pk) 
                TrainingValidation.objects.get(
                    profile = view.user.profile,
                    training = training
                ).delete()

                messages.success(view.request, 
                    _("Training %(training)s has been successfully deleted for %(first_name)s %(last_name)s") % {'training': training.title, 'first_name': view.user.first_name, 'last_name': view.user.last_name}
                )

                view.context = {'training': training}
                html_message = render_to_string('accounts/email/delete_training_validation.html', view.context)

                send_mail(
                    from_email=None,
                    subject=_("Sorry, we cancel your training validation"),
                    message = _("Training deleted"),
                    recipient_list = [view.user.email],
                    html_message = html_message
                )  
