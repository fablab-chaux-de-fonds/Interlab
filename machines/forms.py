from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _


from machines.models import TrainingValidation
from accounts.models import Profile

class TrainingValidationForm(forms.Form):
    validations = forms.BooleanField(required=False)

    def add_new_training_validation(self, view):
         # old:0 -> new:1
        for i in view.new:
            if i not in view.old:
                profile = get_object_or_404(Profile, pk=i)
                TrainingValidation.objects.update_or_create(
                        training = view.training,
                        profile =  profile
                    )
                messages.success(view.request, _(
                    "You successfully validate the training %(title)s for user %(first_name)s %(last_name)s" % 
                    {
                        'title': view.training.title, 
                        'first_name': profile.user.first_name, 
                        'last_name': profile.user.last_name}
                    ))
                
    def remove_training_validation(self, view):
        # old:1 -> new:0
        for i in view.old:
            if i not in view.new:
                TrainingValidation.objects.get(
                        training = view.training,
                        profile =  get_object_or_404(Profile, pk=i)
                ).delete()
                messages.success(view.request, _("You successfully remove the training {training.title} for user {profile.user.first_name} {profile.user.last_name}"))