from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from django.utils.translation import gettext as _

from .models import SuperUserListPluginModel, SuperUserProfile
from .filters import SuperUserFilter

@plugin_pool.register_plugin  # register the plugin
class SuperUserListPluginModel(CMSPluginBase):
    model = SuperUserListPluginModel
    module = _("Accounts")
    name = _("Super user list")
    render_template = "accounts/superuser-list.html"
    cache = False

    def render(self, context, instance, placeholder):
        super_user_profile_filter = SuperUserFilter(context['request'].GET, queryset=SuperUserProfile.objects.all())
        context['form'] = super_user_profile_filter.form
        context['obj']= super_user_profile_filter.qs
        return context