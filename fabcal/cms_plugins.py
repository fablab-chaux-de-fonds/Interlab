import json
import datetime

from babel.dates import format_datetime


from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Value, CharField, F, Subquery, OuterRef
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from .models import WeeklyPluginModel, OpeningSlot, EventSlot, TrainingSlot, CalendarOpeningsPluginModel, EventsListPluginModel, Opening, MachineSlot
from machines.models import Machine

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
        next_week_slots = OpeningSlot.objects.filter(end__gt=now, start__lt= now + datetime.timedelta(days=6)).order_by('start')
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

        opening_slots = OpeningSlot.objects.filter(pk=OuterRef('pk'))
        machine_slots_subquery = MachineSlot.objects.filter(opening_slot=Subquery(opening_slots)).values_list('machine', flat=True)

        # Combine the three queries into one
        events = list(
            OpeningSlot.objects.filter(start__gt=datetime.datetime.now() - timedelta(days=365))
            .annotate(
                type=Value('opening', output_field=CharField()),
                user_firstname=F('user__first_name'),
                username=F('user__username'),
                title=F('opening__title'),
                desc=F('opening__desc'),
                background_color=F('opening__background_color'),
                color=F('opening__color'),
                machines=ArrayAgg('machineslot__machine')
            )
            .values(
                'type',
                'pk',
                'username',
                'user_firstname',
                'start',
                'end',
                'comment',
                'title',
                'desc',
                'background_color',
                'color',
                'machines'
            )
        ) + list(
            EventSlot.objects.filter(start__gt=datetime.datetime.now() - timedelta(days=365))
            .annotate(
                type=Value('event', output_field=CharField()),
                user_firstname=F('user__first_name'),
                username=F('user__username'),
                title=F('event__title'),
                desc=F('event__lead'),
                background_color=F('event__background_color'),
                color=F('event__color')
            )
            .values(
                'type',
                'pk',
                'username',
                'user_firstname',
                'start',
                'end',
                'comment',
                'title',
                'desc',
                'background_color',
                'color'
            )
        ) + list(
            TrainingSlot.objects.filter(start__gt=datetime.datetime.now() - timedelta(days=365))
            .annotate(
                type=Value('training', output_field=CharField()),
                user_firstname=F('user__first_name'),
                username=F('user__username'),
                title=F('training__title'),
                background_color=Value('#ddf9ff', output_field=CharField()),
                color=Value('#0b1783', output_field=CharField())
            )
            .values(
                'type',
                'training__pk',
                'username',
                'user_firstname',
                'start',
                'end',
                'comment',
                'title',
                'background_color',
                'color'
            )
        )


        # Fetch all Machine objects corresponding to machine IDs in events
        machine_ids = set(machine_id for event in events if 'machines' in event for machine_id in event['machines'])
        machines = Machine.objects.filter(pk__in=machine_ids)

        # Create a dictionary to map machine IDs to Machine objects
        machine_mapping = {machine.pk: machine for machine in machines}

        # Iterate over the events and update the 'machines' field
        for event in events:
            if 'machines' in event:
                # Map machine IDs to Machine objects and convert to a list of dictionaries
                machine_list = [{'pk': machine_id, 'title': machine_mapping[machine_id].title, 'category': machine_mapping[machine_id].category} for machine_id in event['machines'] if machine_id]
                # Replace the machine IDs with the list of dictionaries
                event['machines'] = machine_list

            # Append the modified event to the backend dictionary
            backend['events'].append(event)

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
        context = {
            'event_slots': list(EventSlot.objects.filter(end__gte = date.today()).order_by('-start')),
            'past_event_slots': list(EventSlot.objects.filter(end__lt = date.today()).order_by('start'))
        }

        return context