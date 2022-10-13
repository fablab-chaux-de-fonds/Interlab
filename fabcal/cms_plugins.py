import json

from urllib import request
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext as _

from .models import WeeklyPluginModel, OpeningSlot, EventSlot, TrainingSlot, CalendarOpeningsPluginModel, EventsListPluginModel

from datetime import date, timedelta

@plugin_pool.register_plugin  # register the plugin
class WeeklyPluginPublisher(CMSPluginBase):
    model = WeeklyPluginModel  # model where plugin data are saved
    module = _("Fabcal")
    name = _("Weekly view")  # name of the plugin in the interface
    render_template = "fabcal/weekly.html"

    def render(self, context, instance, placeholder):
        context.update({'instance': instance})

        current_week = date.today().isocalendar()[1]
        current_week_slots = OpeningSlot.objects.filter(start__week=current_week)
        
        slots = {}
        day_of_week = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        for day in day_of_week:
            slots[day] = [slot for slot in current_week_slots if slot.get_day_of_the_week() == day]

        
        context.update({'slots': slots, 'day_of_week': day_of_week})

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
                'has_registration': False,
                'img': None
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
                'color': event.event.color,
                'has_registration': event.has_registration,
                'img':  event.event.img.url
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

        context.update({
            'backend': json.dumps(backend, default=str),
            })
        return context


@plugin_pool.register_plugin  # register the plugin
class EventListPluginPublisher(CMSPluginBase):
    model = EventsListPluginModel
    module = _("Fabcal")
    name = _("Event list")  # name of the plugin in the interface
    render_template = "fabcal/events_list.html"

    def render(self, context, instance, placeholder):
        context = {
            'events': list(EventSlot.objects.filter(end__gt = date.today()).order_by('start'))
        }
        return context