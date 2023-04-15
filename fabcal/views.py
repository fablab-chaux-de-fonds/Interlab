from copy import deepcopy
import dateparser
import os

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
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, DeleteView
from django.views.generic.detail import DetailView, SingleObjectMixin

from .forms import OpeningForm, EventForm, TrainingForm, RegisterTrainingForm, MachineReservationForm, RegisterEventForm
from .models import OpeningSlot, EventSlot, TrainingSlot, MachineSlot

from interlab.views import CustomFormView

def get_start_end(self, context):
    # TODO implement in AbstractMachineView
    if self.request.method =='GET':
        if self.crud_state == 'created':
            context['start'] = datetime.fromtimestamp(int(self.kwargs['start'])/1000)
            context['end'] = datetime.fromtimestamp(int(self.kwargs['end'])/1000)
        elif self.crud_state == 'updated':
            context['start'] = self.object.start
            context['end'] = self.object.end
    elif self.request.method =='POST':
        for field in ['start', 'end']:
            if context['form'].errors.get(field) is None:
                context[field] = context['form'].cleaned_data[field]
            else:
                context[field] = getattr(context['object'], field)

    return context

class AbstractMachineView(FormView):
    def form_valid(self, form):

        if form.cleaned_data['opening'] is not None:
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
                    if machine.pk not in form.initial.get('machine', []):
                        form.create_machine_slot(self, machine)
        
        return super().form_valid(form)

class AbstractSlotView(View):
    def get_context_data(self, **kwargs):
        context = super(AbstractSlotView, self).get_context_data(**kwargs) # TODO is it necessary ?
        context = get_start_end(self, context)
        language_code = settings.LANGUAGE_CODE
        context.update({
            'start_date': format_datetime(context['start'], "EEEE d MMMM y", locale=language_code),
            'start_time': format_datetime(context['start'], "H:mm", locale=language_code),
            'end_date': format_datetime(context['end'], "EEEE d MMMM y", locale=language_code),
            'end_time': format_datetime(context['end'], "H:mm", locale=language_code),
        })

        if self.object.is_single_day:
            message_format = _("%(start_date)s <br> %(start_time)s - %(end_time)s")
        else:
            message_format = _("From %(start_date)s at %(start_time)s <br> to %(end_date)s at %(end_time)s ")

        context.update({
            'format_info_datetime': mark_safe(message_format % context)
        })
        if 'unregister' in self.request.path:
            context["email_footer"] = _('We hope to see you back soon !')
        else:
            context["email_footer"] = _('The payment will be made on site')

        return context

    def send_email(self):
        html_message = render_to_string(
            'fabcal/email/confirmation.html',
             self.get_context_data()
             )

        if 'reservation' in self.request.path:
            subject = _('Confirmation of your machine reservation')
        elif 'unregister' in self.request.path:
            subject = _('Confirmation of your unregistration')
        else:
            _('Confirmation of your registration')

        send_mail(
            from_email = None,
            subject = subject,
            message = subject,
            recipient_list = [self.request.user.email],
            html_message = html_message
        )

    def get_success_message(self):
        if 'reservation' in self.request.path:
            context = self.get_context_data()
            message = mark_safe(_('You successfully booked the machine %(machine)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s') % context)
            return messages.success(self.request, message)
        elif 'unregister' in self.request.path:
            return messages.success(self.request, _("Oh no! We sent you an email to confirme your unregistration"))
        else:
            return messages.success(self.request, _("Well done! We sent you an email to confirme your registration"))

    def form_valid(self, form):
        if 'reservation' in self.request.path:
            pass
        elif 'unregister' in self.request.path:
            self.object.registrations.remove(self.request.user)
        else:
            self.object.registrations.add(self.request.user)
        self.send_email()
        self.get_success_message()
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

class OpeningSlotDeleteView(DeleteView):
    model = OpeningSlot
    success_url = '/schedule'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = settings.LANGUAGE_CODE
        context.update({ 
            'date': format_datetime(self.object.start, "EEEE d MMMM y", locale=language_code),
            'start': format_datetime(self.object.start, "H:mm", locale=language_code),
            'end': format_datetime(self.object.end, "H:mm", locale=language_code),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        context = self.get_context_data()

        if not self.object.can_be_deleted:
            messages.error(request, _('This opening slot cannot be deleted.'))
            return redirect(success_url)

        self.object.delete()
        messages.success(request, _("Your opening on %(date)s from %(start)s to %(end)s has been successfully deleted") % context)
        return redirect(success_url)

class EventBaseView(CustomFormView, AbstractMachineView):
    template_name = 'fabcal/event_create_or_update_form.html'
    form_class = EventForm
    crud_state = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['submit_btn'] = _('Create event') if self.crud_state == 'created' else _('Update event')

        context = get_start_end(self, context)
        return context

    def form_valid(self, form):
        response  = super().form_valid(form)
        form.update_or_create_event_slot(self)
        return response

class EventCreateView(EventBaseView):
    crud_state = 'created'

class EventUpdateView(EventBaseView):
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

class EventDeleteView(AbstractSlotView, DeleteView):
    model = EventSlot

    def delete(self, request, *args, **kwargs):
        delete = super().delete(request, *args, **kwargs)
        messages.success(request, _("Your event has been successfully deleted"))
        return delete

    def get_success_url(self):
        return reverse_lazy('pages-details-by-slug', kwargs={'slug': 'schedule'})

class EventDetailView(AbstractSlotView, DetailView):
    model = EventSlot

class RegisterBaseView(LoginRequiredMixin, SingleObjectMixin, AbstractSlotView, CustomFormView):
    def get_context_data(self, **kwargs):
        context = super(RegisterBaseView, self).get_context_data(**kwargs)
        context.update({
            'first_name': self.request.user.first_name
        })
        return context

class EventRegisterBaseView(RegisterBaseView):
    template_name = 'fabcal/eventslot_(un)registration_form.html'
    form_class = RegisterEventForm
    model = EventSlot

    def get_success_url(self):
        return reverse_lazy("fabcal:event-detail", kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super(EventRegisterBaseView, self).get_context_data(**kwargs)
        context.update({
            'href': f"{self.request._current_scheme_host}/fabcal/event/{context['object'].pk}", #TODO refactor with reverse function
            'title': context['object'].event.title,
        })
        return context
        
class EventRegisterView(EventRegisterBaseView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'email_body': \
                mark_safe(_('We confirm that you are registered for the event <a href="%(href)s">%(title)s</a> which will take place on %(start_date)s from %(start_time)s to %(end_time)s.') % context) \
                if context['object'].is_single_day else \
                mark_safe(_('We confirm that you are registered for the event <a href="%(href)s">%(title)s</a> which will take place from %(start_date)s at %(start_time)s to %(end_date)s at %(end_time)s.') % context)
        })

        return context

class EventUnregisterView(EventRegisterBaseView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'email_body': \
                mark_safe( _('We confirme that you are unregister for the event <a href="%(href)s">%(title)s</a> which will take place on %(start_date)s from %(start_time)s to %(end_time)s.') % context) \
                if context['object'].is_single_day else \
                mark_safe(_('We confirme that you are unregister for the event <a href="%(href)s">%(title)s</a> which will take place from %(start_date)s at %(start_time)s to %(end_date)s at %(end_time)s.') % context)
        })

        return context

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

class TrainingCreateView(TrainingBaseView):
    crud_state = 'created'

class TrainingUpdateView(TrainingBaseView):
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

class TrainingDeleteView(AbstractSlotView, DeleteView):
    model = TrainingSlot

    def delete(self, request, *args, **kwargs):
        delete = super().delete(request, *args, **kwargs)
        messages.success(request, _("Your training has been successfully deleted"))
        return delete

    def get_success_url(self):
        return reverse_lazy("machines:training-detail", kwargs={'pk': self.object.training_id})

class TrainingRegisterBaseView(RegisterBaseView):
    template_name = 'fabcal/trainingslot_(un)registration_form.html'
    form_class = RegisterTrainingForm
    model = TrainingSlot

    def get_success_url(self):
        return reverse_lazy("machines:training-detail", kwargs={'pk': self.object.training_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'href': f"{self.request._current_scheme_host}{self.get_success_url()}",
            'title': context['object'].training.title,
        })
        return context

class TrainingRegisterView(TrainingRegisterBaseView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'email_body': mark_safe(_('We confirm that you are registered for the training <a href="%(href)s">%(title)s</a> which will take place on %(start_date)s from %(start_time)s to %(end_time)s.') % context),
        })

        return context

class TrainingUnregisterView(TrainingRegisterBaseView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'email_body': mark_safe(_('We confirm that you are unregistered for the training <a href="%(href)s">%(title)s</a> which will take place on %(start_date)s from %(start_time)s to %(end_time)s.') % context),
        })

        return context

class MachineReservationBaseView(RegisterBaseView):
    template_name = 'fabcal/machine/reservation_form.html'
    form_class = MachineReservationForm
    model = MachineSlot
    crud_state = 'updated'

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
            messages.error(request, _('Sorry, you cannot reserve this machine yet. You have to take the training first before you can use it.'))
            return redirect('/trainings/?machine_category=' + str(self.machine_slot.machine.category.pk))

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['machine_slot'] = self.machine_slot
        kwargs["next_machine_slot"] = self.next_machine_slot
        kwargs["previous_machine_slot"] = self.previous_machine_slot
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(MachineReservationBaseView, self).get_context_data(**kwargs)
        context.update({
            'next_machine_slot' : self.next_machine_slot,
        })
        
        if self.machine_slot.machine.category.name == '3D':
            context["next_machine_slot"] = MachineSlot.objects.filter(
                start__gt = self.machine_slot.start, machine=self.machine_slot.machine, user__isnull=False
                ).order_by('start').first()
            context['max_start_time'] = self.machine_slot.end - timedelta(minutes=settings.FABCAL_MINIMUM_RESERVATION_TIME)
        return context

class CreateMachineReservationView(MachineReservationBaseView):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()
    
    def get_context_data(self, **kwargs):
        context = super(MachineReservationBaseView, self).get_context_data()

        if context['form'].is_valid():
            context.update({
                'machine': self.object.machine.title,
                'duration': int(context['form'].cleaned_data['duration'].seconds/60),
                'profile_url': self.request._current_scheme_host + reverse('profile'),
                'mail_url': 'mailto://' + os.environ.get('EMAIL_HOST_USER')
            })
            context.update({
                'email_body': \
                    mark_safe(_('You successfully booked the machine %(machine)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s') % context),
                'cancellation_policy': \
                    mark_safe(_('Please note that you may cancel this reservation up to 24 hours prior to the start of the slot without charge via your <a href="%(profile_url)s">account page on our website</a>. However, if you wish to cancel your reservation after this period, please <a href="%(mail_url)s">inform us by email</a>. In this case, we are sorry to inform you that we will be obliged to charge you for the machine hours, as the reserved machine could not be used by another person at that time. Thank you for your understanding.') % context)
            })
        return context
    
    
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