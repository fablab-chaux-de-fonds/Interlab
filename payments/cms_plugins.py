from cms.plugin_base import CMSPluginBase
from djangocms_text_ckeditor.cms_plugins import TextPlugin
from cms.plugin_pool import plugin_pool

from django.utils.translation import gettext as _

from .models import CheckoutButtonPluginModel

@plugin_pool.register_plugin
class CheckoutButtonPluginPublisher(CMSPluginBase):
    model = CheckoutButtonPluginModel
    module = _("Interlab")
    name = _("Subscription Button")
    render_template = "payments/button.html"
    text_enabled = True

    def render(self, context, instance, placeholder):
        context.update({'instance': instance})
        return super().render(context, instance, placeholder)