import json

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import gettext_lazy as _
from .models import TypewriterPlugin
from .forms import TypewriterPluginForm

@plugin_pool.register_plugin
class TypewriterCMSPlugin(CMSPluginBase):
    model = TypewriterPlugin
    name = _("Typewriter Plugin")
    render_template = "plugins/typewriter_plugin.html"
    form = TypewriterPluginForm

    def render(self, context, instance, placeholder):
        strings_list = instance.strings.split(',')
        context.update({
            'instance': instance,
            'strings': json.dumps(strings_list),
        })
        return context