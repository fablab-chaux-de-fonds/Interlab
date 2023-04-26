from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy

class SuperuserRequiredMixin(UserPassesTestMixin):
    """
    Mixin to require a user to be logged in and a superuser in a group,
    and redirect to login if not.
    """
    login_url = reverse_lazy('login')

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.groups.filter(name='superuser').exists()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            next_url = self.request.get_full_path()
            login_url = f'{self.login_url}?next={next_url}'
            return redirect(login_url)
        else:
            raise PermissionDenied
