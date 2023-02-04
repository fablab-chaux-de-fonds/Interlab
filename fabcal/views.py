from copy import deepcopy
import dateparser

from babel.dates import format_datetime

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template import loader
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views import View

from .forms import OpeningForm, EventForm, TrainingForm, RegistrationTrainingForm, MachineReservationForm
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
        try:
            context['start'] = super(type(context['form']), context['form']).clean_start()
        except ValidationError:
            context['start'] = context['form'].initial['start']

        try:
            context['end'] = super(type(context['form']), context['form']).clean_end()
        except ValidationError:
            context['end'] = context['form'].initial['end']

    return context

class AbstractMachineView(FormView):
    def form_valid(self, form):

        if form.cleaned_data['opening'] != None:
            self.opening_slot = form.update_or_create_opening_slot(self)

            if self.crud_state == 'created':
                # TODO: check if machine slot already exists
                for machine in form.cleaned_data['machine']:
                    form.create_machine_slot(self, machine)

            elif self.crud_state == 'updated':
                # Remove machine slot
                for pk in form.initial.get('machine', []):
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

class OpeningBaseView(CustomFormView, AbstractMachineView):
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

        messages.success(request, 
            _("Your opening on %(date)s from %(start)s to %(end)s has been successfully deleted") % 
            { 
                'date': opening_slot.start.strftime("%A %d %B %Y"), 
                'start': opening_slot.start.strftime("%H:%M"), 
                'end': opening_slot.end.strftime("%H:%M") 
                }
            )
        return redirect('/schedule/')

class EventBaseView(CustomFormView, AbstractMachineView):
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
        response  = super().form_valid(form)
        form.update_or_create_event_slot(self)
        return response

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
        #Refactoring with event queryset
        context = {
            'event_slot': get_object_or_404(EventSlot, pk=self.kwargs['pk'])
        }
        return render(request, self.template_name, context)

# Refactoring with TemplateView + get_context_data
class RegisterEventBaseView(LoginRequiredMixin, View):

    def get_event_slot(self, pk):
        return EventSlot.objects.get(pk=pk)

    def get(self, request, pk, *args, **kwargs):
        context = self.get_context(request, pk)
        return render(request, self.template_name, context)

    def get_context(self, request, pk):
        event_slot = self.get_event_slot(pk)
        return {
            'event_slot': event_slot,
            'request': request
        }

    def get_mail_context(self, request, pk, message_format):
            event_slot = self.get_event_slot(pk)
            context = {
                'first_name': request.user.first_name,
                'href': f"{request._current_scheme_host}/fabcal/event/{event_slot.pk}",
                'title': event_slot.event.title,
                'start_date': format_datetime(event_slot.start, "EEEE d MMMM y", locale=settings.LANGUAGE_CODE),
                'start_time': format_datetime(event_slot.start, "H:mm", locale=settings.LANGUAGE_CODE), 
                'end_date': format_datetime(event_slot.end, "EEEE d MMMM y", locale=settings.LANGUAGE_CODE),
                'end_time': format_datetime(event_slot.end, "H:mm", locale=settings.LANGUAGE_CODE), 
            }
            context['email_body'] = mark_safe( message_format % context)
            return context

class RegisterEventView(RegisterEventBaseView):
    template_name = 'fabcal/event_registration_form.html'

    def post(self, request, pk, *args, **kwargs):
        event_slot = self.get_event_slot(pk)
        event_slot.registrations.add(request.user)

        if event_slot.is_single_day:
            message_format = _('We confirme that you are register for the event <a href="%(href)s">%(title)s</a> which will take place on %(start_date)s from %(start_time)s to %(end_time)s.')
        else:
            message_format = _('We confirme that you are register for the event <a href="%(href)s">%(title)s</a> which will take place from %(start_date)s at %(start_time)s to %(end_date)s at %(end_time)s.')

        context = self.get_mail_context(request, pk, message_format)
        context['email_footer'] = _('The payment will be made on site')

        html_message = render_to_string('fabcal/email/event_(un)registration_confirmation.html', context)
        
        send_mail(
            from_email=None,
            subject=_('Confirmation of your registration'),
            message = _("Confirmation of your registration"),
            recipient_list = [request.user.email],
            html_message = html_message
        )

        messages.success(request, _("Well done! We sent you an email to confirme your registration"))

        return redirect('fabcal:show-event', pk)
    
class UnregisterEventView(RegisterEventBaseView):
    template_name = 'fabcal/event_unregistration_form.html'

    def post(self, request, pk, *args, **kwargs):
        event_slot = self.get_event_slot(pk)
        event_slot.registrations.remove(request.user)

        if event_slot.is_single_day:
            message_format = _('We confirme that you are unregister for the event <a href="%(href)s">%(title)s</a> which will take place on %(start_date)s from %(start_time)s to %(end_time)s.')
        else:
            message_format = _('We confirme that you are unregister for the event <a href="%(href)s">%(title)s</a> which will take place from %(start_date)s at %(start_time)s to %(end_date)s at %(end_time)s.')

        context = self.get_mail_context(request, pk, message_format)
        context['email_footer'] = _('We hope to see you back soon !')

        html_message = render_to_string('fabcal/email/event_(un)registration_confirmation.html', context)
        
        send_mail(
            from_email=None,
            subject=_('Confirmation of your unregistration'),
            message = _("Confirmation of your unregistration"),
            recipient_list = [request.user.email],
            html_message = html_message
        )

        messages.success(request, _("Oh no! We sent you an email to confirme your unregistration"))

        return redirect('fabcal:show-event', pk)

class TrainingBaseView(CustomFormView, AbstractMachineView): 
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

        # Create training
        training_slot = form.update_or_create_training_slot(self)

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
    template_name = 'fabcal/training/delete.html'

    def get(self, request, pk, *args, **kwargs):
        event = TrainingSlot.objects.get(pk=pk)
        # Refactoring with event queryset
        context = {
            'start': event.start,
            'end': event.end,
            'title': event.training.title
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
        context = {
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
        form.send_mail(self)
        return super().form_valid(form)

class UnregisterTrainingView(LoginRequiredMixin, View):
    template_name = 'fabcal/training/unregistration.html'
    success_url = "/"

    def get(self, request, pk, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        return {
            'training_slot': get_object_or_404(TrainingSlot, pk=self.kwargs['pk'])
        }

    def post(self, request, pk, *args, **kwargs):
        context = self.get_context_data()

        context['training_slot'].registrations.remove(request.user)
        html_message = render_to_string('fabcal/email/training_unregistration_confirmation.html', context)
        
        send_mail(
            from_email=None,
            subject=_('Confirmation of your unregistration'),
            message = _("Confirmation of your unregistration"),
            recipient_list = [request.user.email],
            html_message = html_message
        )

        messages.success(request, _("Oh no! We sent you an email to confirme your unregistration"))

        return redirect('profile')

class MachineReservationBaseView(LoginRequiredMixin, FormView):
    template_name = 'fabcal/machine/reservation_form.html'
    form_class = MachineReservationForm

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('/accounts/login?next=%s' % request.path)

        self.machine_slot = get_object_or_404(MachineSlot, pk=self.kwargs['pk'])
        self.next_machine_slot = MachineSlot.objects.filter(
                start__gt = self.machine_slot.start, machine=self.machine_slot.machine, user__isnull=False
                ).order_by('start').first()

        self.previous_machine_slot = MachineSlot.objects.filter(
                start__lt = self.machine_slot.start, machine=self.machine_slot.machine, user__isnull=False
                ).order_by('start').last()

        self.next_free_machine_slot = MachineSlot.objects.filter(
                start__gt = self.machine_slot.start, machine=self.machine_slot.machine, user__isnull=True
                ).order_by('start').first()

        self.previous_free_machine_slot = MachineSlot.objects.filter(
                start__lt = self.machine_slot.start, machine=self.machine_slot.machine, user__isnull=True
                ).order_by('start').last()

        # Check if user is trained
        if self.request.user.profile.pk not in self.machine_slot.machine.trained_profile_list:
            messages.error(request, _('Sorry, you cannont reserve this machine, because you need to complete the training before using it'))
            return redirect('/trainings/?machine_category=' + str(self.machine_slot.machine.category.pk))

        return super(MachineReservationBaseView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(MachineReservationBaseView, self).get_form_kwargs()
        kwargs['machine_slot'] = self.machine_slot
        kwargs["next_machine_slot"] = self.next_machine_slot
        kwargs["previous_machine_slot"] = self.previous_machine_slot
        return kwargs

    def get_initial(self):
        try:
            initial = {
                'start_time': self.request._post['start_time'],
                'end_time': self.request._post['end_time'],
            }
            if self.machine_slot.machine.category.name == '3D':
               initial['end_date']= dateparser.parse(self.request._post['end_date']).strftime('%Y-%m-%d')

        except:
            initial = {
                'start_time': self.machine_slot.start.strftime('%H:%M'),
                'end_time': self.machine_slot.end.strftime('%H:%M'),
            }
            if self.machine_slot.machine.category.name == '3D':
               initial['end_date']= self.machine_slot.end.strftime('%Y-%m-%d')

        return initial

    def get_context_data(self, **kwargs):
        context = super(MachineReservationBaseView, self).get_context_data(**kwargs)
        context["machine_slot"] = self.machine_slot
        context["next_machine_slot"] = self.next_machine_slot

        if self.machine_slot.machine.category.name == '3D':
            context["next_machine_slot"] = MachineSlot.objects.filter(
                start__gt = self.machine_slot.start, machine=self.machine_slot.machine, user__isnull=False
                ).order_by('start').first()
            context['max_start_time'] = self.machine_slot.end - timedelta(minutes=settings.FABCAL_MINIMUM_RESERVATION_TIME)
        return context

class CreateMachineReservationView(MachineReservationBaseView): 
    
    def get_success_url(self, **kwargs):
        return reverse('machines:machines-show', kwargs = {'pk': self.machine_slot.machine.pk})

    def form_valid(self, form):

        if form.machine_slot.start < form.cleaned_data['start']:
            # create a new empty slot at the begining
            new_slot = deepcopy(form.machine_slot)
            new_slot.id = None
            new_slot.end = form.cleaned_data['start']
            new_slot.save()
        
        if form.machine_slot.end > form.cleaned_data['end']:
            # create a new empty slot at the end
            new_slot = deepcopy(form.machine_slot)
            new_slot.id = None
            new_slot.start = form.cleaned_data['end']
            new_slot.save()

        if self.machine_slot.machine.category.name == '3D':
            for slot in MachineSlot.objects.filter(
                start__gt=form.cleaned_data['start'], 
                end__gt=form.cleaned_data['end'],
                machine=self.machine_slot.machine).all():
                    # create a new empty slot at the end
                    slot.start = form.cleaned_data['end']
                    slot.save()

            for slot in MachineSlot.objects.filter(
                start__gt=form.cleaned_data['start'], 
                end__lt=form.cleaned_data['end'],
                machine=self.machine_slot.machine).all():
                # delete slot
                slot.delete()

        # update slot for user
        form.machine_slot.user = self.request.user
        form.machine_slot.start = form.cleaned_data['start']
        form.machine_slot.end = form.cleaned_data['end']
        form.machine_slot.save()

        # send mail and message
        self.context = {
            'machine_slot': self.machine_slot,
            'request': self.request
        }
        form.send_mail(self)
        form.message(self)

        return super().form_valid(form)

class UpdateMachineReservationView(MachineReservationBaseView):
    def get_success_url(self, **kwargs):
        return reverse('profile')

    def form_valid(self, form):

        # start modification
        #===================

        if form.cleaned_data['start'] > form.machine_slot.start:
            if form.machine_slot.start == form.machine_slot.opening_slot.start:
                start = form.machine_slot.opening_slot.start
            
            elif form.machine_slot.start == self.previous_machine_slot.end:
                start = self.previous_machine_slot.end

            # create new slot
            MachineSlot.objects.create(
                opening_slot = self.machine_slot.opening_slot,
                machine = self.machine_slot.machine,
                start = start,
                end = form.cleaned_data['start'],
            )


        if form.cleaned_data['start'] != form.machine_slot.start:
            # adjust the previous slot end
            if self.previous_free_machine_slot:
                if self.previous_free_machine_slot.end == form.machine_slot.start:
                    self.previous_free_machine_slot.end = form.cleaned_data['start']
                    self.previous_free_machine_slot.save()

                # delete free slot if start = end
                if self.previous_free_machine_slot.start == self.previous_free_machine_slot.end:
                    self.previous_free_machine_slot.delete()

            # adjust start slot
            form.machine_slot.start = form.cleaned_data['start']
            form.machine_slot.save()


        


        # end modification
        #=================
        if form.cleaned_data['end'] < form.machine_slot.end:
            if form.machine_slot.end == form.machine_slot.opening_slot.end:
                end = form.machine_slot.opening_slot.end
            
            elif form.machine_slot.end == self.next_machine_slot.start:
                end = self.next_machine_slot.start

            # create new slot
            MachineSlot.objects.create(
                opening_slot = self.machine_slot.opening_slot,
                machine = self.machine_slot.machine,
                start = form.cleaned_data['end'],
                end = end,
            )

        if form.cleaned_data['end'] != form.machine_slot.end:
            # adjust the next slot start
            if self.next_free_machine_slot:
                if self.next_free_machine_slot.start == form.machine_slot.end:
                    self.next_free_machine_slot.start = form.cleaned_data['end']
                    self.next_free_machine_slot.save()

                # delete free slot if start = end
                if self.next_free_machine_slot.start == self.next_free_machine_slot.end:
                    self.next_free_machine_slot.delete()

            # adjust end
            form.machine_slot.end = form.cleaned_data['end']
            form.machine_slot.save()         

        return super().form_valid(form)

class DeleteMachineReservationView(TemplateView):
    template_name = 'fabcal/machine/delete_form.html'

    def get_success_url(self, **kwargs):
        return reverse('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['machine_slot'] = get_object_or_404(MachineSlot, pk=self.kwargs['pk'])
        return context

    def post(self, request, pk):
        obj = get_object_or_404(MachineSlot, pk=self.kwargs['pk'])
        obj.user = None
        obj.save()
        
        messages.success(request, _("You reservation has been canceled !"))
        return redirect('profile') 

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