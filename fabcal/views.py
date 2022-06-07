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

from .forms import CreateOpeningForm
from .models import OpeningSlot
from openings.models import Opening

# Create your views here.
class CreateOpeningView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    form_class = CreateOpeningForm
    template_name = 'fabcal/create_opening.html'

    def get(self, request, *args, **kwargs):
        items = []
        for item in list(Opening.objects.all()):
            items.append(
                {
                    'text': item.title,
                    'value': item.pk
                }
            )

        context = {
            'form': CreateOpeningForm(),
            'initial': {
                    'opening': 1,
                    'start': datetime.fromtimestamp(int(self.kwargs['start'])/1000),
                    'end': datetime.fromtimestamp(int(self.kwargs['end'])/1000),
                    'items': items
            },
        }
        return render(request, self.template_name, context)

    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        form.data = form.data.copy()
        form.data['start'] = dateparser.parse(form.data['date'] + 'T' + form.data['start'])
        form.data['end'] = dateparser.parse(form.data['date'] + 'T' + form.data['end'])

        if form.is_valid():
            start = form.cleaned_data['start']
            end = form.cleaned_data['end']
            opening = form.cleaned_data['opening']
            OpeningSlot(
                start=start,
                end=end,
                opening=opening,
                comment=form.cleaned_data['comment'],
                user_id = request.user.id
                ).save()
            messages.success(request, mark_safe(
                _("Your slot has been successfully created on ") + 
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