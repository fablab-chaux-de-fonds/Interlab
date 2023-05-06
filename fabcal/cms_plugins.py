import json
import datetime

from babel.dates import format_datetime


from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from .models import WeeklyPluginModel, OpeningSlot, EventSlot, TrainingSlot, CalendarOpeningsPluginModel, EventsListPluginModel, Opening

from datetime import date, timedelta

@plugin_pool.register_plugin  # register the plugin
class WeeklyPluginPublisher(CMSPluginBase):
    model = WeeklyPluginModel  # model where plugin data are saved
    module = _("Fabcal")
    name = _("Weekly view")  # name of the plugin in the interface
    render_template = "fabcal/weekly.html"

    def render(self, context, instance, placeholder):
        context.update({'instance': instance})

        now = datetime.datetime.now()
        next_week_slots = OpeningSlot.objects.filter(end__gt=now, start__lt= now + datetime.timedelta(days=7)).order_by('start')
        weekdays = [(now + datetime.timedelta(days=x)).strftime('%A') for x in range(7)]

        slots = {}
        for weekday in weekdays:
            slots[weekday] = [slot for slot in next_week_slots if slot.get_day_of_the_week == weekday]

        context.update({'slots': slots, 'weekdays': weekdays})

        return context

@plugin_pool.register_plugin  # register the plugin
class CalendarOpeningsPluginPublisher(CMSPluginBase):
    model = CalendarOpeningsPluginModel
    module = _("Fabcal")
    name = _("Calendar openings view")  # name of the plugin in the interface
    render_template = "fabcal/opening_calendar.html"

    def render(self, context, instance, placeholder):
        request = context['request']

        backend = {}
        backend['events'] = []

        events = list(OpeningSlot.objects.filter(start__gt = date.today() - timedelta(days=365) ))
        for event in events:
            backend['events'].append({
                'type': 'opening',
                'pk': event.pk,
                'username': event.user.username,
                'user_firstname': event.user.first_name,
                'start': event.start,
                'end': event.end,
                'comment': event.comment,
                'title': event.opening.title,
                'desc': event.opening.desc,
                'background_color': event.opening.background_color,
                'color': event.opening.color,
                'machines': [{'pk': i.pk, 'title': i.title, 'category': i.category} for i in event.get_machine_list]
            })

        events = list(EventSlot.objects.filter(start__gt = date.today() - timedelta(days=365) ))
        for event in events:
            backend['events'].append({
                'type': 'event',
                'pk': event.pk,
                'username': event.user.username,
                'user_firstname': event.user.first_name,
                'start': event.start,
                'end': event.end,
                'comment': event.comment,
                'title': event.event.title,
                'desc': event.event.lead,
                'background_color': event.event.background_color,
                'color': event.event.color
            })

        events = list(TrainingSlot.objects.filter(start__gt = date.today() - timedelta(days=365) ))
        for event in events:
            backend['events'].append({
                'type': 'training',
                'pk': event.training.pk,
                'username': event.user.username,
                'user_firstname': event.user.first_name,
                'start': event.start,
                'end': event.end,
                'comment': event.comment,
                'title': event.training.title,
                'background_color': '#ddf9ff',
                'color': '#0b1783',
                })
        
        backend["is_superuser"] = request.user.groups.filter(name='superuser').exists()
        backend["username"] = request.user.username

        context = {
            'backend': json.dumps(backend, default=str),
            'public_openings': Opening.objects.filter(is_public=True)
            }
        return context


@plugin_pool.register_plugin  # register the plugin
class EventListPluginPublisher(CMSPluginBase):
    model = EventsListPluginModel
    module = _("Fabcal")
    name = _("Event list")  # name of the plugin in the interface
    render_template = "fabcal/events_list.html"

    def render(self, context, instance, placeholder):
        language_code = settings.LANGUAGE_CODE
        context = {
            'event_slots': list(EventSlot.objects.filter(end__gt = date.today()).order_by('start'))
        }

        for index, event in enumerate(context['event_slots']):
            # TODO Refactoring wigh fabcal -> data in model

            context['event_slots'][index].start_date = format_datetime(event.start, "EEEE d MMMM y", locale=language_code)
            context['event_slots'][index].start_time = format_datetime(event.start, "H:mm", locale=language_code)
            context['event_slots'][index].end_date = format_datetime(event.end, "EEEE d MMMM y", locale=language_code)
            context['event_slots'][index].end_time = format_datetime(event.end, "H:mm", locale=language_code)

            if event.is_single_day:
                message_format = _("%(start_date)s <br> %(start_time)s - %(end_time)s")
            else:
                message_format = _("From %(start_date)s at %(start_time)s <br> to %(end_date)s at %(end_time)s ")

            context['event_slots'][index].format_info_datetime = mark_safe(message_format % context['event_slots'][index].__dict__)

        return context