from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from django.utils.translation import gettext as _

from .models import Training, TrainingsListPluginModel, MachinesListPluginModel, MachineGroup, Machine
from .filters import MachineFilter, TrainingFilter


@plugin_pool.register_plugin  # register the plugin
class TrainingsListPluginPublisher(CMSPluginBase):
    model = TrainingsListPluginModel
    module = _("Machines")
    name = _("training list")
    render_template = "trainings/list.html"
    cache = False

    def render(self, context, instance, placeholder):
        training_filter = TrainingFilter(context['request'].GET, queryset=Training.objects.filter(is_active=True).order_by('machine_category'))
        context['form'] = training_filter.form
        context['trainings'] =training_filter.qs
        return context

@plugin_pool.register_plugin
class MachinesListPluginPublisher(CMSPluginBase):
    model = MachinesListPluginModel
    module = _("Machines")
    name = _("Machine list")
    render_template = "machines/list.html"
    cache = False

    def render(self, context, instance, placeholder):
        machine_filter = MachineFilter(context['request'].GET, queryset=Machine.objects.all().order_by('title'))
        context['form'] = machine_filter.form
        context['machines']= machine_filter.qs
        context['groups']= MachineGroup.objects.all().order_by('sort')
        
        return context