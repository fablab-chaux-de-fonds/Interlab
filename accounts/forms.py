import smtplib

from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from organizations.forms import OrganizationUserAddForm
from organizations.backends import invitation_backend

from django_registration.forms import RegistrationForm

from .models import SubscriptionCategory

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
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)

            ############################################
            # Check if user active before check password
            # https://github.com/django/django/blob/main/django/contrib/auth/forms.py
            User = get_user_model()
            user = User.objects.get(username=username)

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

class UserSubcriptionForm(forms.Form):
    subscription_category = forms.ChoiceField(
        choices=[('no-subscription', _('No Subscription'))] + [(x.pk, x.title) for x in SubscriptionCategory.objects.all()], 
        widget=forms.RadioSelect)
