from django.contrib.auth.mixins import AccessMixin

class SuperuserRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.groups.filter(name='superuser').exists():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)