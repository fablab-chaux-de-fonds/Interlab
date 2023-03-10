from django.core.exceptions import BadRequest

class ProfileRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.profile is None:
            raise BadRequest("missing profile")
        return super().dispatch(request, *args, **kwargs)