from datetime import datetime, timedelta
from babel.dates import format_datetime

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponseForbidden, HttpResponse, QueryDict, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import loader
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormView, DeleteView, CreateView, UpdateView
from django.views.generic.detail import DetailView, SingleObjectMixin

from interlab.views import CustomFormView

from .forms import OpeningSlotCreateForm
from .forms import OpeningSlotUpdateForm
from .forms import MachineSlotUpdateForm
from .forms import TrainingSlotCreateForm
from .forms import TrainingSlotUpdateForm
from .forms import TrainingSlotRegistrationCreateForm
from .forms import TrainingSlotRegistrationDeleteForm
from .forms import EventSlotCreateForm
from .forms import EventSlotUpdateForm
from .forms import EventSlotRegistrationCreateForm
from .forms import EventSlotRegistrationDeleteForm
from .forms import EventForm
from .forms import RegisterEventForm

from .models import OpeningSlot, EventSlot, TrainingSlot, MachineSlot
from .mixins import SuperuserRequiredMixin


def get_start_end(self, context):
    # TODO implement in AbstractMachineView
    if self.request.method =='GET':
        if self.crud_state == 'updated':
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
            context["email_footer"] = _('The payment will be done on the spot by card or in cash')

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

class UserView(LoginRequiredMixin, SuccessMessageMixin, CustomFormView):
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
            
        # Pass the user object to the form's constructor
        return form_class(self.request.user, **self.get_form_kwargs())

class CreateSlotView(UserView, CreateView):
    def get_initial(self):
        initial = super().get_initial()
        
        params = {}
        for i in ['start', 'end']:
            params[i] = datetime.fromtimestamp(int(self.kwargs.get(i))/1000)

        initial['date'] = params['start'].strftime('%Y-%m-%d')
        initial['start_time'] = params['start'].strftime('%H:%M')
        initial['end_time'] = params['end'].strftime('%H:%M')
        return initial

class UpdateSlotView(UserView, UpdateView):

    def get_initial(self):
        initial = super().get_initial()
        initial['start'] = self.object.start
        initial['end'] = self.object.end

        initial['date'] = self.object.start.strftime('%Y-%m-%d')
        initial['start_time'] = self.object.start.strftime('%H:%M')
        initial['end_time'] = self.object.end.strftime('%H:%M')
        return initial

class RegisterSlotView(UserView, UpdateView):
    pass

class DeleteSlotView(LoginRequiredMixin, DeleteView):

    def dispatch(self, request, *args, **kwargs):
        slot = self.get_object()
        # Check if the request user is not the same as the machine slot user
        if request.user != slot.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = settings.LANGUAGE_CODE
        context.update({ 
            'date': format_datetime(self.object.start, "EEEE d MMMM y", locale=language_code),
            'start': format_datetime(self.object.start, "H:mm", locale=language_code),
            'end': format_datetime(self.object.end, "H:mm", locale=language_code),
        })
        return context

class OpeningSlotView(SuperuserRequiredMixin):
    model = OpeningSlot
    success_url = '/schedule/'

    success_message = _("Your opening has been successfully %(action)s on %(date)s from %(start_time)s to %(end_time)s </br> "
                 "<a href=\"/fabcal/download-ics-file/%(opening_title)s/%(start)s/%(end)s\"> "
                 "<i class=\"bi bi-file-earmark-arrow-down-fill\"> </i> Add to my calendar</a>")

    def get_success_message(self, cleaned_data):
        if issubclass(self.__class__, CreateView):
            action = _('created')
        elif issubclass(self.__class__, UpdateView):
            action = _('updated')

        return self.success_message % dict(
                    action=action,
                    date=self.object.formatted_start_date,
                    start_time=self.object.formatted_start_time,
                    end_time=self.object.formatted_end_time,
                    opening_title=self.object.opening.title,
                    start=self.object.start,
                    end=self.object.end
                )

    def form_invalid(self, form):       
        updated_data = QueryDict(mutable=True)
        updated_data.update(form.data)

        for error in form.errors.get('__all__').data:

            if error.code == 'conflicting_openings':        
                conflicting_openings = error.params.get('conflicting_openings')

                # Calculate the new start and end time based on the existing opening
                for conflicting_opening in conflicting_openings:

                    # Determine the start time of the new opening based on the conflicting opening
                    # If the new opening starts before the conflicting opening, use the start time of the new opening
                    # Otherwise, use the end time of the conflicting opening
                    if form.cleaned_data['start_time'] < conflicting_opening.start.time():
                        start_time = form.cleaned_data['start_time']
                    else:
                        start_time = conflicting_opening.end.time()

                    # Determine the end time of the new opening based on the conflicting opening
                    # If the new opening ends after the conflicting opening, use the end time of the new opening
                    # Otherwise, use the start time of the conflicting opening
                    if form.cleaned_data['end_time'] > conflicting_opening.end.time():
                        end_time = form.cleaned_data['end_time']
                    else:
                        end_time = conflicting_opening.start.time()


                # Set the form data to the new start and end time
                updated_data['start_time'] = forms.TimeField().prepare_value(start_time)
                updated_data['end_time'] = forms.TimeField().prepare_value(end_time)

                # Call form.add_error to add the error to the start_time field
                form.add_error('start_time', error)


            elif error.code == 'conflicting_reservation':
                updated_data['start_time'] = forms.TimeField().prepare_value(
                    datetime.strptime(form.initial['start_time'], '%H:%M').time()
                    )
                updated_data['end_time'] = forms.TimeField().prepare_value(
                    datetime.strptime(form.initial['end_time'], '%H:%M').time()
                    )

        # Update form data
        form.data = updated_data

        # Return the invalid form
        return self.render_to_response(self.get_context_data(form=form))

class OpeningSlotCreateView(OpeningSlotView, CreateSlotView):
    form_class = OpeningSlotCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_btn'] = _('Create opening')
        return context

class OpeningSlotUpdateView(OpeningSlotView, UpdateSlotView):
    form_class = OpeningSlotUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_btn'] = _('Update opening')
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial['machines'] = [i.pk for i in self.object.get_machine_list]
        return initial

class OpeningSlotDeleteView(SuperuserRequiredMixin, DeleteSlotView):
    model = OpeningSlot
    success_url = '/schedule'
    sucess_message = _("Your opening on %(date)s from %(start)s to %(end)s has been successfully deleted")

    def delete(self, request, *args, **kwargs):
        try:
            super(OpeningSlotDeleteView, self).delete(self, request, *args, **kwargs)
        except ValidationError as e:
            messages.error(request, _(e.message))
            return redirect(self.get_success_url())

        messages.success(request, _("Your opening on %(date)s from %(start)s to %(end)s has been successfully deleted") % self.get_context_data())
        return redirect(self.get_success_url())

class MachineSlotUpdateView(UpdateSlotView):
    model = MachineSlot
    form_class = MachineSlotUpdateForm

    success_message = _('You successfully booked the machine %(machine)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

    def get_success_url(self):
        return reverse_lazy("accounts:profile")

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
                    machine=self.object.machine.title,
                    duration=self.object.get_duration,
                    start_date=self.object.formatted_start_date,
                    start_time=self.object.formatted_start_time,
                    end_time=self.object.formatted_end_time,
                )

    def dispatch(self, request, *args, **kwargs):
        """
        Check if the user's profile is in the trained profile list of a specific machine. 
        If not, display an error message and redirect the user to the training page for that machine category.
        """

        machine_slot = self.get_object()

        if (
            self.request.user.profile.pk not in machine_slot.machine.trained_profile_list
        ):
            messages.error(
                request,
                _(
                    "Sorry, you cannot reserve this machine yet. You have to take the training first before you can use it."
                ),
            )
            return redirect(
                "/trainings/?machine_category="
                + str(machine_slot.machine.category.pk)
            )

        return super().dispatch(request, *args, **kwargs)

class MachineSlotDeleteView(DeleteSlotView):
    model = MachineSlot

    def delete(self, request, pk):
        """
        Deletes a machine slot, adjusts adjacent slots if they are unoccupied, and cancels the user's reservation.
        """
        machine_slot = self.get_object()
        next_machine_slot = machine_slot.next_slots(machine_slot.end + timedelta(minutes=1)).first()
        previous_machine_slot = machine_slot.previous_slots(machine_slot.start - timedelta(minutes=1)).first()

        if next_machine_slot and next_machine_slot.user is None:
            machine_slot.end = next_machine_slot.end
            next_machine_slot.delete()
        
        if previous_machine_slot and previous_machine_slot.user is None:
            machine_slot.start = previous_machine_slot.start
            previous_machine_slot.delete()

        machine_slot.user = None
        machine_slot.save()
        
        messages.success(request, _("You reservation has been deleted !"))
        return redirect('accounts:profile') 

class TrainingSlotView():
    model = TrainingSlot

    def get_success_url(self):
        return reverse('accounts:profile')

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
                    training=self.object.training.title,
                    duration=self.object.get_duration,
                    start_date=self.object.formatted_start_date,
                    start_time=self.object.formatted_start_time,
                    end_time=self.object.formatted_end_time,
                )

class TrainingSlotCreateView(SuperuserRequiredMixin, TrainingSlotView, CreateSlotView):
    form_class = TrainingSlotCreateForm
    success_message = _('You successfully created the training %(training)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

class TrainingSlotUpdateView(SuperuserRequiredMixin, TrainingSlotView, UpdateSlotView):
    form_class = TrainingSlotUpdateForm
    success_message = _('You successfully updated the training %(training)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_btn'] = _('Update training')
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial['machines'] = [i.pk for i in self.object.opening_slot.get_machine_list]
        return initial

class TrainingSlotDeleteView(SuperuserRequiredMixin, DeleteSlotView):
    model = TrainingSlot
    sucess_message = _("Your training on %(date)s from %(start)s to %(end)s has been successfully deleted")

    def get_success_url(self):
        return reverse('machines:training-detail', kwargs={'pk': self.object.training.pk})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(request, self.sucess_message % self.get_context_data())
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            error_code = getattr(e, 'code')
            request.session['error_code'] = error_code
            messages.error(request, e.message)
            return redirect(request.META.get('HTTP_REFERER', '/'))

class TrainingSlotRegistrationView(TrainingSlotView, RegisterSlotView):
    template_name = 'fabcal/trainingslot_(un)registration_form.html'

    def get_success_url(self):
        return reverse_lazy("machines:training-detail", kwargs={'pk': self.object.training_id})

class TrainingSlotRegistrationCreateView(TrainingSlotRegistrationView):
    form_class = TrainingSlotRegistrationCreateForm
    success_message = _('You successfully registered the training %(training)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user in self.object.registrations.all():
            messages.success(request, _('You are already registered for this training slot'))
            return redirect('machines:training-detail', pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

class TrainingSlotRegistrationDeleteView(TrainingSlotRegistrationView):
    form_class = TrainingSlotRegistrationDeleteForm
    success_message = _('You successfully unregistered the training %(training)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user not in self.object.registrations.all():
            return HttpResponseForbidden("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)

class EventDetailView(DetailView):
    model = EventSlot

class EventSlotView():
    model = EventSlot

    def get_success_url(self):
        return reverse('fabcal:eventslot-detail', kwargs={'pk': self.object.pk})

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
                    event=self.object.event.title,
                    duration=self.object.get_duration,
                    start_date=self.object.formatted_start_date,
                    start_time=self.object.formatted_start_time,
                    end_time=self.object.formatted_end_time,
                )

class EventSlotCreateView(SuperuserRequiredMixin, EventSlotView, CreateSlotView):
    form_class = EventSlotCreateForm
    success_message = _('You successfully created the event %(event)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

class EventSlotUpdateView(SuperuserRequiredMixin, EventSlotView, UpdateSlotView):
    form_class = EventSlotUpdateForm
    success_message = _('You successfully updated the event %(event)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_btn'] = _('Update event')
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial['machines'] = [i.pk for i in self.object.opening_slot.get_machine_list]
        return initial

class EventSlotDeleteView(SuperuserRequiredMixin, DeleteSlotView):
    model = EventSlot
    sucess_message = _("Your event on %(date)s from %(start)s to %(end)s has been successfully deleted")

    def get_success_url(self):
        return reverse('fabcal:eventslot-detail', kwargs={'pk': self.object.event.pk})

    def delete(self, request, *args, **kwargs): #TODO create a common method with TrainingSlotDeleteView
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(request, self.sucess_message % self.get_context_data())
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            error_code = getattr(e, 'code')
            request.session['error_code'] = error_code
            messages.error(request, e.message)
            return redirect(request.META.get('HTTP_REFERER', '/'))

class EventSlotRegistrationView(EventSlotView, RegisterSlotView):
    template_name = 'fabcal/eventslot_(un)registration_form.html'

    def get_success_url(self):
        return reverse_lazy("fabcal:eventslot-detail", kwargs={'pk': self.object.event_id})

class EventSlotRegistrationCreateView(EventSlotRegistrationView):
    form_class = EventSlotRegistrationCreateForm
    success_message = _('You successfully registered the event %(event)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user in self.object.registrations.all():
            messages.success(request, _('You are already registered for this event'))
            return redirect('fabcal:eventslot-detail', pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

class EventSlotRegistrationDeleteView(EventSlotRegistrationView):
    form_class = EventSlotRegistrationDeleteForm
    success_message = _('You successfully unregistered the event %(event)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s')

    def dispatch(self, request, *args, **kwargs): #TODO create a common method with EventSlotRegistrationDeleteView
        self.object = self.get_object()
        if request.user not in self.object.registrations.all():
            return HttpResponseForbidden("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)

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
        return reverse_lazy("fabcal:eventslot-detail", kwargs={'pk': self.kwargs['pk']})

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

class MachineReservationListView(LoginRequiredMixin, ListView):
    Model = MachineSlot
    paginate_by = 100

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.groups.filter(name='superuser').exists():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class MachinePastReservationListView(MachineReservationListView):
    def get_queryset(self):
        now = datetime.now().date()
        return MachineSlot.objects.filter(user__isnull=False, end__lt=now).order_by('-start')

class MachineFutureReservationListView(MachineReservationListView):

    def get_queryset(self):
        now = datetime.now().date()
        return MachineSlot.objects.filter(user__isnull=False, end__gte=now).order_by('start')

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
