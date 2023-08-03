from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from django.utils.translation import gettext as _

from .models import SuperUserListPluginModel, SuperUserPorfile

@plugin_pool.register_plugin  # register the plugin
class SuperUserListPluginModel(CMSPluginBase):
    model = SuperUserListPluginModel
    module = _("Accounts")
    name = _("Super user list")
    render_template = "accounts/superuser-list.html"

    def render(self, context, instance, placeholder):
        context = super(SuperUserListPluginModel, self).render(context, instance, placeholder)
        context['obj'] = SuperUserPorfile.objects.all()
        return context