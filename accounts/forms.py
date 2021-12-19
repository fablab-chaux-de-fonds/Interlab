import smtplib

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext_lazy as _

from organizations.forms import OrganizationUserAddForm
from organizations.backends import invitation_backend

from django_registration.forms import RegistrationForm

class EditProfileForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        del self.fields['password']

    class Meta:
        model = User
        fields = ('first_name','last_name','username','email',)

        
class CustomOrganizationUserAddForm(OrganizationUserAddForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        if self.organization.users.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                _("There is already an organization " "member with this email address!")
            )
        if get_user_model().objects.filter(email__iexact=email).count() > 1:
            raise forms.ValidationError(
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
            raise forms.ValidationError(
                _("Recipient address rejected: Domain not found")
            )

        return email

class CustomRegistrationForm(RegistrationForm):
    "This form is used for registration - Base class form Django"
    class Meta(RegistrationForm.Meta):
            model = get_user_model()
            fields = ['first_name','last_name','username','email','password1','password2']

class CustomUserRegistrationForm(CustomRegistrationForm):
    "This form is used when the user in invited with django-organization"
    email = forms.EmailField(widget=forms.TextInput(
        attrs={'class': 'disabled', 'readonly': 'readonly'}))