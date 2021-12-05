from django.urls import reverse
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import gettext as _

from .models import Profile
from organizations.backends.defaults import InvitationBackend

import inspect

class CustomInvitations(InvitationBackend):
    """
    A backend for inviting new users to join the site as members of an
    organization.
    """
    def get_success_url(self):
        return reverse("profile")

    def invite_by_email(self, email, sender=None, request=None, **kwargs):
        """Creates an inactive user with the information we know and then sends
        an invitation email for that user to complete registration.
        If your project uses email in a different way then you should make to
        extend this method as it only checks the `email` attribute for Users.
        """
        try:
            user = self.user_model.objects.get(email=email)
        except self.user_model.DoesNotExist:
            # TODO break out user creation process
            if (
                "username"
                in inspect.getfullargspec(self.user_model.objects.create_user).args
            ):
                user = self.user_model.objects.create(
                    username=email,
                    email=email,
                    password=self.user_model.objects.make_random_password(),
                )
            else:
                user = self.user_model.objects.create(
                    email=email, password=self.user_model.objects.make_random_password()
                )
            user.is_active = False
            user.save()
        self.send_invitation(user, sender, **kwargs)
        return user