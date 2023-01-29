from django.db import models
from django.utils.translation import ugettext as _
from cms.plugin_base import CMSPlugin
from accounts.models import SubscriptionCategory

class CheckoutButtonPluginModel(CMSPlugin):
    subscription_category = models.ForeignKey(SubscriptionCategory, on_delete=models.CASCADE, null=True)
    text = models.CharField(max_length=64, null=True, default=None, blank=True)
    
    def __unicode__(self):
        return u"{}".format(self)

    def __str__(self):
        if self.text is not None:
            return self.text
        elif self.subscription_category is not None:
            return self.subscription_category.title
        else:
            return _('Checkout')
    
