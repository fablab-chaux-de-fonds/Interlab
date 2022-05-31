from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext as _

from .models import WeeklyPluginModel, OpeningSlot

from datetime import date

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