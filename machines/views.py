import datetime


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import Training, ToolTraining, TrainingValidation, TrainingNotification, Machine
from .forms import TrainingValidationForm

from fabcal.models import TrainingSlot, MachineSlot

# TODO change to DetailView
def training_show(request, pk):
    training = get_object_or_404(Training, pk=pk)

    if request.user.is_authenticated:
        notification = TrainingNotification.objects.filter(profile=request.user.profile, training=training).exists()
        if request.method == 'POST':
            if notification:
                # user has already the notification and want to unsuscribe
                TrainingNotification.objects.get(profile=request.user.profile, training=training).delete()
                messages.success(request, _("Oh no! you unsubsribe from notification"))
            else:
                TrainingNotification.objects.update_or_create(profile = request.user.profile, training=training)
                messages.success(request, _("Thanks for interest, we will contact you as soon as possible"))
            
            #update notification variable 
            notification = TrainingNotification.objects.filter(profile__user=request.user, training=training).exists()

    else: 
        notification = False

    context = {
        'training': training,
        'training_slots': TrainingSlot.objects.filter(training__pk = pk, start__gte=datetime.datetime.now()).order_by('start'),
        'machines': training.machines_list,
        'tools': ToolTraining.objects.filter(training__pk=pk).order_by('sort'),
        'notification': notification,
        'interested_user_count': TrainingNotification.objects.filter(training=training).count()
        }

    return render(request, 'trainings/show.html', context)


class TrainingValidationView(LoginRequiredMixin, FormView):
    template_name = 'trainings/training_validation.html'
    form_class = TrainingValidationForm
    success_url = "/" # TODO redirect to training show view

    def get_context_data(self, **kwargs):
        training_slot = get_object_or_404(TrainingSlot, pk=self.kwargs['pk'])
        registrations = training_slot.registrations.all()
        graduates = [i.profile for i in TrainingValidation.objects.filter(training__pk=training_slot.training.pk)]

        context = {
            'registrations': registrations,
            'graduates': graduates,
            'training': training_slot.training,
            'training_slot': training_slot
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

@login_required
def training_waiting_list(request, pk):
    context = {
        'training_notifications': TrainingNotification.objects.filter(training__pk=pk).all().order_by('modified_date'),
        'training': get_object_or_404(Training, pk=pk)
    }
    return render(request, 'trainings/waiting_list.html', context)

class MachineShowView(DetailView):
    template_name = 'machines/show.html'
    model = Machine

    def get_context_data(self, **kwargs):
        context = super(MachineShowView, self).get_context_data(**kwargs)
        
        next_opening_slots = []
        for i in MachineSlot.objects.filter(machine=context['machine'], end__gt=datetime.datetime.now()).order_by('start'):
            if i.opening_slot not in next_opening_slots:
                next_opening_slots.append(i.opening_slot)

        context['next_opening_slots'] = next_opening_slots
        context['FABCAL_MINIMUM_RESERVATION_TIME'] = settings.FABCAL_MINIMUM_RESERVATION_TIME
        context['FABCAL_RESERVATION_INCREMENT_TIME'] = settings.FABCAL_RESERVATION_INCREMENT_TIME
        return context

class MachineSlotView(MachineShowView):
    template_name = 'machines/mobile_slots.html'