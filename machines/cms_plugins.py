from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from django.utils.translation import gettext as _

from .models import Training, TrainingsListPluginModel


@plugin_pool.register_plugin  # register the plugin
class TrainingsListPluginPublisher(CMSPluginBase):
    model = TrainingsListPluginModel
    module = _("Machines")
    name = _("training list")  # name of the plugin in the interface
    render_template = "trainings/list.html"

    def render(self, context, instance, placeholder):
        context = {
            'trainings': list(Training.objects.filter(is_active=True))
        }
        return context