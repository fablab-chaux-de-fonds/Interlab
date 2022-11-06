from curses import init_pair
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template import loader
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views import View

from .forms import OpeningForm, EventForm, TrainingForm, RegistrationTrainingForm
from .models import OpeningSlot, EventSlot, TrainingSlot, MachineSlot

from interlab.views import CustomFormView

def get_start_end(self, context):
    if self.request.method =='GET':
        if self.crud_state == 'created':
            context['start'] = datetime.fromtimestamp(int(self.kwargs['start'])/1000)
            context['end'] = datetime.fromtimestamp(int(self.kwargs['end'])/1000)
        elif self.crud_state == 'updated':
            if self.type == 'opening':
                slot = OpeningSlot.objects.get(pk=self.kwargs['pk'])
            elif self.type == 'event':
                slot = EventSlot.objects.get(pk=self.kwargs['pk'])
            elif self.type == 'training':
                slot = TrainingSlot.objects.get(pk=self.kwargs['pk'])
            context['start'] = slot.start
            context['end'] = slot.end
    elif self.request.method =='POST':
            context['start'] = super(OpeningForm, context['form']).clean_start()
            context['end'] = super(OpeningForm, context['form']).clean_end()

    return context

class OpeningBaseView(CustomFormView):
    template_name = 'fabcal/opening_create_or_update_form.html'
    form_class = OpeningForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.crud_state == 'created':
            context['submit_btn'] = _('Create opening')
        elif self.crud_state == 'updated':
            context['submit_btn'] = _('Update opening')

        context = get_start_end(self, context)
        return context

    def form_valid(self, form):
        # add user_id in cleaned_data
        form.cleaned_data['user_id'] = self.request.user.id
        self.opening_slot = form.update_or_create_opening_slot(self)

        if self.crud_state == 'created':
            for machine in form.cleaned_data['machine']:
                form.create_machine_slot(self, machine)

        elif self.crud_state == 'updated':
            # Remove machine slot
            for pk in form.initial['machine']:
                if pk not in form.cleaned_data['machine'].values_list('pk', flat=True):
                    form.delete_machine_slot(self, pk)

            # Update machine slot
            for machine in form.cleaned_data['machine']:
                qs = MachineSlot.objects.filter(
                        opening_slot=self.opening_slot,
                        machine = machine
                ).order_by('start')

                if form.cleaned_data['start'] < form.initial['start']:
                    # extend start opening before
                    obj = qs.first()
                    if obj.user:
                        # create new slot to not modify user reservation
                        MachineSlot.objects.create(
                            opening_slot = self.opening_slot,
                            machine = machine,
                            start = form.cleaned_data['start'],
                            end = form.initial['start'],
                        )
                    else:
                        # exend slot
                        obj.start = form.cleaned_data['start']
                        obj.save()

                # shorten or remove start slots
                if form.cleaned_data['start'] > form.initial['start']:
                    for obj in qs:
                        if obj.start < form.cleaned_data['start']:
                            
                            # shorten start slot
                            if obj.end > form.cleaned_data['start']:
                                obj.start = form.cleaned_data['start']
                                obj.save()
                            
                            # remove start slot
                            else:
                                obj.delete()

                # shorten or remove start slots
                if form.cleaned_data['end'] < form.initial['end']:
                    for obj in qs:
                        if obj.end > form.cleaned_data['end']:
                            
                            # shorten start slot
                            if obj.start < form.cleaned_data['end']:
                                obj.end = form.cleaned_data['end']
                                obj.save()
                            
                            # remove start slot
                            else:
                                obj.delete()

                if form.cleaned_data['end'] > form.initial['end']:
                    # extend end opening after
                    obj = qs.last()

                    if obj.user:
                        # create new slot to not modify user reservation
                        MachineSlot.objects.create(
                            opening_slot = self.opening_slot,
                            machine = machine,
                            start = form.initial['end'],
                            end = form.cleaned_data['end'],
                        )
                    else:
                        # exend slot
                        obj.end = form.cleaned_data['end']
                        obj.save()

            # Create a new machine slot
            for machine in form.cleaned_data['machine']:
                if machine.pk not in form.initial['machine']:
                    form.create_machine_slot(self, machine)
        
        return super().form_valid(form)

class CreateOpeningView(OpeningBaseView):
    crud_state = 'created'

class UpdateOpeningView(OpeningBaseView):
    crud_state = 'updated'
    type = 'opening'

    def get_initial(self):
        opening_slot = OpeningSlot.objects.get(pk=self.kwargs['pk'])
        initial = opening_slot.__dict__
        initial['opening'] = opening_slot.opening
        
        machine_slot = MachineSlot.objects.filter(opening_slot = opening_slot)
        machine = {i.machine.pk for i in machine_slot}
        initial['machine'] = machine
        return initial

class DeleteOpeningView(View):
    template_name = 'fabcal/delete_opening.html'

    def get(self, request, pk, *args, **kwargs):
        opening = OpeningSlot.objects.get(pk=pk)
        context = {
            'start': opening.start,
            'end': opening.end,
            }
        return render(request, self.template_name, context)  

    def post(self, request, pk):
        opening_slot = OpeningSlot.objects.get(pk=pk)
        opening_slot.delete()

        messages.success(request, (
                _("Your opening has been successfully deleted on ") + 
                opening_slot.start.strftime("%A %d %B %Y") + 
                _(" from ") +
                opening_slot.start.strftime("%H:%M") + 
                _(" to ") + 
                opening_slot.end.strftime("%H:%M")
                )
            ) 
        return redirect('/schedule/')

class EventBaseView(CustomFormView):
    template_name = 'fabcal/event_create_or_update_form.html'
    form_class = EventForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.crud_state == 'created':
            context['submit_btn'] = _('Create event')
        elif self.crud_state == 'updated':
            context['submit_btn'] = _('Update event')

        context = get_start_end(self, context)
        return context

    def form_valid(self, form):
        # add user_id in cleaned_data
        form.cleaned_data['user_id'] = self.request.user.id
        
        if form.cleaned_data['opening']:
            opening_slot = form.update_or_create_opening_slot(self)
        else: 
            opening_slot = None
        
        form.update_or_create_event_slot(self, opening_slot)


        return super().form_valid(form)

class CreateEventView(EventBaseView):
    crud_state = 'created'

class UpdateEventView(EventBaseView):
    crud_state = 'updated'
    type = 'event'

    def get_initial(self):
        event_slot = EventSlot.objects.get(pk=self.kwargs['pk'])
        initial = event_slot.__dict__
        initial['event'] = event_slot.event
        try:
            initial['opening'] = event_slot.opening_slot.opening
        except AttributeError:
            initial['opening'] = None
        return initial

class DeleteEventView(View):
    template_name = 'fabcal/delete_event.html'

    def get(self, request, pk, *args, **kwargs):
        event = EventSlot.objects.get(pk=pk)
        # Refactoring with event queryset
        context = {
            'start': event.start,
            'end': event.end,
            'title': event.event.title
            }
        return render(request, self.template_name, context)  

    def post(self, request, pk):
        event_slot = EventSlot.objects.get(pk=pk)
        event_slot.delete()

        messages.success(request, (
                _("Your event has been successfully deleted on ") + 
                event_slot.start.strftime("%A %d %B %Y") + 
                _(" from ") +
                event_slot.start.strftime("%H:%M") + 
                _(" to ") + 
                event_slot.end.strftime("%H:%M")
                )
            ) 
        return redirect('/schedule/')  

class DetailEventView(View):
    template_name = 'fabcal/event_details.html'

    def get(self, request, pk, *args, **kwargs):
        event = EventSlot.objects.get(pk=pk)
        #Refactoring with event queryset
        context = {
            'pk': event.pk,
            'title': event.event.title,
            'img': event.event.img,
            'lead': event.event.lead,
            'desc': event.event.desc,
            'start': event.start,
            'end': event.end,
            'price': event.price,
            'location': event.event.location,
            'has_registration': event.has_registration,
            'is_registration_open': event.is_registration_open, 
            'registrations': event.registrations.all(),
            'is_single_day': event.is_single_day,
            'available_registration': event.available_registration
        }
        return render(request, self.template_name, context)

# Refactoring with TemplateView + get_context_data
class RegisterEventBaseView(LoginRequiredMixin, View):

    def get(self, request, pk, *args, **kwargs):
        context = self.get_context(request, pk)
        return render(request, self.template_name, context)

    def get_context(self, request, pk):
        event = EventSlot.objects.get(pk=pk)
        #Refactoring with event queryset
        return {
                'pk': event.pk,
                'title': event.event.title,
                'start': event.start,
                'end': event.end,
                'price': event.price,
                'location': event.event.location,
                'has_registration': event.has_registration,
                'first_name': request.user.first_name,
                'is_single_day': event.is_single_day,
                'href': request.scheme + '://' + request.get_host() + '/fabcal/event/' + str(pk)
            }

class RegisterEventView(RegisterEventBaseView):
    template_name = 'fabcal/event_registration_form.html'

    def post(self, request, pk, *args, **kwargs):
        event = EventSlot.objects.get(pk=pk)
        event.registrations.add(request.user)

        context = self.get_context(request, pk)
        html_message = render_to_string('fabcal/email/event_registration_confirmation.html', context)
        
        send_mail(
            from_email=None,
            subject=_('Confirmation of your registration'),
            message = _("Confirmation of your registration"),
            recipient_list = [request.user.email],
            html_message = html_message
        )

        messages.success(request, _("Well done! We sent you an email to confirme your registration"))

        return redirect('show-event', pk)
    
class UnregisterEventView(RegisterEventBaseView):
    template_name = 'fabcal/event_unregistration_form.html'

    def post(self, request, pk, *args, **kwargs):
        event = EventSlot.objects.get(pk=pk)
        event.registrations.remove(request.user)

        context = self.get_context(request, pk)
        html_message = render_to_string('fabcal/email/event_unregistration_confirmation.html', context)
        
        send_mail(
            from_email=None,
            subject=_('Confirmation of your unregistration'),
            message = _("Confirmation of your unregistration"),
            recipient_list = [request.user.email],
            html_message = html_message
        )

        messages.success(request, _("Oh no! We sent you an email to confirme your unregistration"))

        return redirect('event', pk)

class TrainingBaseView(CustomFormView): 
    template_name = 'fabcal/trainig_create_or_update_form.html'
    form_class = TrainingForm
    type = 'training'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.crud_state == 'created':
            context['submit_btn'] = _('Create training')
        elif self.crud_state == 'updated':
            context['submit_btn'] = _('Update training')

        context = get_start_end(self, context)
        return context

    def form_valid(self, form):
        # add user_id in cleaned_data
        form.cleaned_data['user_id'] = self.request.user.id
        
        # Create opening
        if form.cleaned_data['opening']:
            opening_slot = form.update_or_create_opening_slot(self)
        else: 
            opening_slot = None
        
        # Create training
        training_slot = form.update_or_create_training_slot(self, opening_slot)

        # Alert users
        self.context = {
            'training_slot': training_slot,
            'request': self.request
        }
        form.alert_users(self)

        return super().form_valid(form)

class CreateTrainingView(TrainingBaseView):
    crud_state = 'created'

class UpdateTrainingView(TrainingBaseView):
    crud_state = 'updated'

    def get_initial(self):
        training_slot = TrainingSlot.objects.get(pk=self.kwargs['pk'])
        initial = training_slot.__dict__
        initial['training'] = training_slot.training
        try:
            initial['opening'] = training_slot.opening_slot.opening
        except AttributeError:
            initial['opening'] = None
        return initial

class DeleteTrainingView(View):
    template_name = 'fabcal/delete_training.html'

    def get(self, request, pk, *args, **kwargs):
        event = TrainingSlot.objects.get(pk=pk)
        # Refactoring with event queryset
        context = {
            'start': event.start,
            'end': event.end,
            'title': event.event.title
            }
        return render(request, self.template_name, context)  

    def post(self, request, pk):
        event_slot = TrainingSlot.objects.get(pk=pk)
        event_slot.delete()

        messages.success(request, (
                _("Your event has been successfully deleted on ") + 
                event_slot.start.strftime("%A %d %B %Y") + 
                _(" from ") +
                event_slot.start.strftime("%H:%M") + 
                _(" to ") + 
                event_slot.end.strftime("%H:%M")
                )
            ) 
        return redirect('/schedule/') 

class RegisterTrainingView(LoginRequiredMixin, FormView):
    template_name = 'fabcal/training_registration_form.html'
    form_class = RegistrationTrainingForm
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        training_slot = get_object_or_404(TrainingSlot, pk=self.kwargs['pk'])
        context ={
            'training_slot': training_slot,
            'training': training_slot.training
        }
        return context

    def form_valid(self, form):
        self.context = {
            'training_slot': get_object_or_404(TrainingSlot, pk=self.kwargs['pk']),
            'request': self.request
        }

        form.register(self)
        form.send_email(self)
        return super().form_valid(form)


class downloadIcsFileView(TemplateView):
    template_name = 'fabcal/fablab.ics'

    def get(self, request, summary, start, end, *args, **kwargs):
        context = {
            'start': start,
            'end': end, 
            'summary': summary
        }
        response =  HttpResponse(
            loader.get_template(self.template_name).render(context, request),
            content_type="text/plain"
        )
        response['Content-Disposition'] = 'attachment; filename="fablab.ics"'
        return response