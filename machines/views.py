import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView


from .models import Training, ToolTraining, TrainingValidation
from .forms import TrainingValidationForm

from fabcal.models import TrainingSlot

def trainings_list(request):
    trainings = Training.objects.all()

    return render(request, 'trainings/list.html', {'trainings': trainings})

def training_show(request, pk):
    training = get_object_or_404(Training, pk=pk)

    if request.user.is_authenticated:
        notification = training.notification.filter(user = request.user).exists()
        if request.method == 'POST':
            if notification:
                # user has already the notification and want to unsuscribe
                training.notification.remove(request.user.profile)
                messages.success(request, _("Oh no! you unsubsribe from notification"))
            else:
                training.notification.add(request.user.profile)
                messages.success(request, _("Thanks for interest, we will contact you as soon as possible"))
            
            #update notification variable 
            notification = training.notification.filter(user = request.user).exists()

    else: 
        notification = False

    training_slots = TrainingSlot.objects.filter(training__pk = pk, start__gte=datetime.datetime.now())
    tools = [tool_training.tool for tool_training in ToolTraining.objects.filter(training__pk=pk).order_by('sort')]

    context = {
        'training': training,
        'training_slots': training_slots,
        'machines': training.machines_list,
        'tools': tools,
        'notification': notification
        }

    return render(request, 'trainings/show.html', context)


class trainingValidation(LoginRequiredMixin, FormView):
    template_name = 'trainings/training_validation.html'
    form_class = TrainingValidationForm
    success_url = "/"

    def get_context_data(self, **kwargs):
        training_slot = get_object_or_404(TrainingSlot, pk=self.kwargs['pk'])
        registrations = training_slot.registrations.all()
        graduates = [i.profile for i in TrainingValidation.objects.filter(training__pk=training_slot.training.pk)]

        context = {
            'registrations': registrations,
            'graduates': graduates,
            'training': training_slot.training
        }

        return context


    def form_valid(self, form, **kwargs):
            context = self.get_context_data(**kwargs)
            self.old = [graduate.pk for graduate in context['graduates']] # list of initial Profile pk checked
            self.new = self.request.POST.getlist('validations') # list of checked Profile pk after validation
            self.training = context['training']

            form.add_new_training_validation(self)
            form.remove_training_validation(self)

            return redirect('/')
