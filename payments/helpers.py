import datetime
from accounts.models import Subscription, SubscriptionCategory

class SubscriptionDurationHelper:
    def __init__(self, subscription_category:SubscriptionCategory, subscription:Subscription):
        self.different_category = False
        self.start = datetime.date.today()
        self.current_subscription_remaining_days = 0
        if subscription is not None:
            if subscription.subscription_category.id != subscription_category.id:
                self.different_category = True
            elif subscription.end > self.start:
                self.current_subscription_remaining_days = (subscription.end - self.start).days
        self.new_subscription_days = subscription_category.duration
        self.end = self.start + datetime.timedelta(days=self.new_subscription_days + self.current_subscription_remaining_days)