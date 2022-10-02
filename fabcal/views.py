import dateparser
import json

from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin 
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.template.defaultfilters import date as _date
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views import View

from .forms import OpeningForm, EventForm
from .models import OpeningSlot, EventSlot
from openings.models import Opening



def get_opening_items():
    return [{'text': item.title, 'value': item.pk} for item in list(Opening.objects.all())]

class OpeningBaseView(LoginRequiredMixin, UserPassesTestMixin, View ):
    form_class = OpeningForm
    opening_items = get_opening_items()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        form.data = form.data.copy()
        form.data['start'] = dateparser.parse(form.data['date'] + 'T' + form.data['start_time'])
        form.data['end'] = dateparser.parse(form.data['date'] + 'T' + form.data['end_time'])
        
        try:
            pk = kwargs['pk']
        except:
            pk = None 

        for field in form:
            print("Field Error:", field.name,  field.errors)

        if form.is_valid():
            start = form.cleaned_data['start']
            end = form.cleaned_data['end']
            opening = form.cleaned_data['opening']
            OpeningSlot.objects.update_or_create(
                pk=pk,
                defaults={
                    'start': start,
                    'end': end,
                    'opening': opening,
                    'comment': form.cleaned_data['comment'],
                    'user_id' :  request.user.id
                    }
                )
            messages.success(request, mark_safe(
                _("Your opening has been successfully %(crud_state)s on") % {'crud_state': _(self.crud_state)} + 
                _date(start, "l d F Y") + 
                _(" from ") +
                start.strftime("%H:%M") + 
                _(" to ") + 
                end.strftime("%H:%M") + 
                "</br>" +
                "<a href=\"/fabcal/download-ics-file/" + opening.title + "/" + start.strftime("%Y%m%dT%H%M%S%z")  + "/" + end.strftime("%Y%m%dT%H%M%S%z")  + "/\" download>" + 
                "<i class=\"bi bi-file-earmark-arrow-down-fill\"></i> " + 
                _('Download .ICS file') +
                 "</a>"
                )
            ) 
            return redirect('/schedule/')

    def test_func(self):
        return self.request.user.groups.filter(name='superuser').exists()

class CreateOpeningView(OpeningBaseView):
    template_name = 'fabcal/create_opening.html'
    crud_state = 'created'

    def get(self, request, *args, **kwargs):
        context = {
            'form': OpeningForm(),
            'backend': json.dumps(
                {
                    'opening': 1,
                    'start': datetime.fromtimestamp(int(self.kwargs['start'])/1000).isoformat(),
                    'end': datetime.fromtimestamp(int(self.kwargs['end'])/1000).isoformat(),
                    'opening_items': self.opening_items
                }
            ),
        }
        return render(request, self.template_name, context)


class UpdateOpeningView(OpeningBaseView):
    template_name = 'fabcal/update_opening.html'
    crud_state = 'updated'

    def get(self, request, pk, *args, **kwargs):
        opening = OpeningSlot.objects.get(pk=pk)
        context = {
            'form': OpeningForm(),
            'backend': json.dumps(
                {
                    'opening': opening.opening.pk,
                    'start': opening.start,
                    'end': opening.end,
                    'opening_items': self.opening_items
                },
                default=str
            )
        }
        return render(request, self.template_name, context)  

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


class EventBaseView(FormView):
    template_name = 'fabcal/event_create_or_update_form.html'
    form_class = EventForm
    success_url = '/schedule/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.crud_state == 'created':
            context['submit_btn'] = _('Create event')
        elif self.crud_state == 'updated':
            context['submit_btn'] = _('Update event')

        for field in context['form'].fields:
            if not 'class' in context['form'][field].field.widget.attrs:
                context['form'][field].field.widget.attrs['class'] = 'form-control'

            if context['form'][field].widget_type == 'select':
                context['form'][field].field.widget.attrs['class'] += ' form-select'

        if self.request.method =='POST':
            context['start'] = context['form'].cleaned_data['start']
            context['end'] = context['form'].cleaned_data['end']
        else:
            if self.crud_state == 'created':
                context['start'] = datetime.fromtimestamp(int(self.kwargs['start'])/1000)
                context['end'] = datetime.fromtimestamp(int(self.kwargs['end'])/1000)
            elif self.crud_state == 'updated':
                event = EventSlot.objects.get(pk=self.kwargs['pk'])
                context['start'] = event.start
                context['end'] = event.end
        return context

    def form_invalid(self, form):
        for field in form.errors:
            if field != '__all__':
                form[field].field.widget.attrs['class'] = 'form-control is-invalid'
        return super().form_invalid(form)

    def form_valid(self, form):
        
        # add user_id in cleaned_data
        form.cleaned_data['user_id'] = self.request.user.id
        
        form.update_or_create_event_slot(self)

        if form.cleaned_data['opening']:
            form.update_or_create_opening_slot(self)

        return super().form_valid(form)

class CreateEventView(EventBaseView):
    crud_state = 'created'
class UpdateEventView(EventBaseView):
    crud_state = 'updated'

    def get_initial(self):
        return EventSlot.objects.get(pk=self.kwargs['pk']).__dict__

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