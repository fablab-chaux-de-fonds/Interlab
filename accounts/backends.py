import inspect
from urllib import request

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.urls import reverse

from .models import Profile
from .forms import CustomUserRegistrationForm

from organizations.backends.defaults import InvitationBackend

from newsletter.views import register_email

class CustomInvitationsBackend(InvitationBackend):
    """
    A backend for inviting new users to join the site as members of an
    organization.
    """

    form_class = CustomUserRegistrationForm

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

            # link profile / account / organization / subscription if user already exist
            Profile.objects.update_or_create(user=user, defaults={'subscription':sender.profile.subscription})

        except:
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
            
            # Link profile / user if user not exist yet
            profile = Profile(user=user, subscription=sender.profile.subscription)
            profile.save()

        self.send_invitation(user, sender, **kwargs)
        return user


    def activate_view(self, request, user_id, token):
        """
        View function that activates the given User by setting `is_active` to
        true if the provided information is verified.
        """
        try:
            user = self.user_model.objects.get(id=user_id, is_active=False)
        except self.user_model.DoesNotExist:
            return redirect('invitations-token-error')

        if not PasswordResetTokenGenerator().check_token(user, token):
            return redirect('invitations-token-error')

        if not user.organizations_organization.first(): 
            return redirect('invitations-token-error')

        form = self.get_form(
             data=request.POST or None, files=request.FILES or None, instance=user
        )

        if form.is_valid():
            form.instance.is_active = True
            if form.cleaned_data['newsletter']: 
                register_email(form.cleaned_data['email'])
            user = form.save()
            user.set_password(form.cleaned_data["password1"])
            user.save()
            self.activate_organizations(user)
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password1"],
            )

            login(request, user)
            return redirect(self.get_success_url())

        context = {
            "form": form,
            "organization": user.organizations_organization.first()
        }
        return render(request, self.registration_form_template, context)

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
            return
        except UserModel.MultipleObjectsReturned:
            user = UserModel.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user