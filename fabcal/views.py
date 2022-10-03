from curses import init_pair
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views import View

from .forms import OpeningForm, EventForm
from .models import OpeningSlot, EventSlot

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
            context['start'] = slot.start
            context['end'] = slot.end
    elif self.request.method =='POST':
        context['start'] = context['form'].cleaned_data['start']
        context['end'] = context['form'].cleaned_data['end']
    return context

class CustomFormView(FormView):
    success_url = '/schedule/'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for field in context['form'].fields:
            if not 'class' in context['form'][field].field.widget.attrs:
                context['form'][field].field.widget.attrs['class'] = 'form-control'

            if context['form'][field].widget_type == 'select':
                context['form'][field].field.widget.attrs['class'] += ' form-select'
        return context

    def form_invalid(self, form):
        for field in form.errors:
            if field != '__all__':
                form[field].field.widget.attrs['class'] = 'form-control is-invalid'
        return super().form_invalid(form)

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
        form.update_or_create_opening_slot(self)
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
        initial['opening'] = event_slot.opening_slot.opening
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