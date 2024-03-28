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

from .models import OpeningSlot, EventSlot, TrainingSlot, MachineSlot
from .mixins import SuperuserRequiredMixin


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
