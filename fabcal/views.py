from tracemalloc import start
import dateparser

from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin 
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views import View

from .forms import OpeningForm
from .models import OpeningSlot
from openings.models import Opening


class OpeningBaseView(View, LoginRequiredMixin, UserPassesTestMixin):
    form_class = OpeningForm
    items = [{'text': item.title, 'value': item.pk} for item in list(Opening.objects.all())]

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        form.data = form.data.copy()
        form.data['start'] = dateparser.parse(form.data['date'] + 'T' + form.data['start'])
        form.data['end'] = dateparser.parse(form.data['date'] + 'T' + form.data['end'])
        
        try:
            pk = kwargs['pk']
        except:
            pk = None 

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
                _("Your slot has been successfully %(crud_state) on") % {'crud_state': self.crud_state} + 
                form.cleaned_data['start'].strftime("%A %d %B %Y") + 
                _(" from ") +
                form.cleaned_data['start'].strftime("%H:%M") + 
                _(" to ") + 
                form.cleaned_data['end'].strftime("%H:%M") + 
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
            'initial': {
                    'opening': 1,
                    'start': datetime.fromtimestamp(int(self.kwargs['start'])/1000),
                    'end': datetime.fromtimestamp(int(self.kwargs['end'])/1000),
                    'items': self.items
            },
        }
        return render(request, self.template_name, context)


class UpdateOpeningView(OpeningBaseView):
    template_name = 'fabcal/update_opening.html'
    crud_state = 'updated'

    def get(self, request, pk, *args, **kwargs):
        opening = OpeningSlot.objects.get(pk=pk)
        context = {
            'form': OpeningForm(),
            'initial': {
                    'opening': opening.opening.pk,
                    'start': opening.start,
                    'end': opening.end,
                    'items': self.items
            },
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
                _("Your slot has been successfully deleted on ") + 
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