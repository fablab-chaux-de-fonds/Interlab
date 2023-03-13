import stripe
import datetime

from babel.dates import format_datetime, get_timezone

from django.urls import reverse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView


from .forms import CreateCheckoutSessionForm
from .helpers import SubscriptionDurationHelper
from accounts.mixins import ProfileRequiredMixin
from accounts.models import Profile, Subscription, SubscriptionCategory

class SubscriptionUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "payments/subscription_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        actual_subscription = None
        if self.request.user.profile is not None \
            and self.request.user.profile.subscription is not None:
            actual_subscription = self.request.user.profile.subscription
        
        selected_category = None
        if 'category_id' not in kwargs:
            subscription_categories = SubscriptionCategory.objects.all().order_by('sort', 'star_flag')
            if len(subscription_categories) <= 0:
                return context
            context['available_categories'] = subscription_categories
            if actual_subscription is not None:
                selected_category = actual_subscription.subscription_category
            else:
                selected_category = subscription_categories.first()
        else:
            selected_category = SubscriptionCategory.objects.get(pk=kwargs['category_id'])
        
        context['currency'] = settings.STRIPE_CURRENCY
        
        context['selected_category'] = selected_category
        context['helper'] = SubscriptionDurationHelper(selected_category, actual_subscription)
        
        return context

class SubscriptionUpdateSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "payments/subscription_update_success.html"

class SubscriptionUpdateCancelView(LoginRequiredMixin, TemplateView):
    template_name = "payments/subscription_update_cancel.html"
    
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)

class CreateCheckoutSessionFormView(LoginRequiredMixin, ProfileRequiredMixin, FormView):
    form_class = CreateCheckoutSessionForm

    def form_valid(self, form):
        session = StripeCheckoutSession()
        return session.create(self.request, form.cleaned_data['category_id'])

class StripeCheckoutSession:
    def create(self, request:HttpRequest, category_id:int) -> HttpResponse:
        category = SubscriptionCategory.objects.get(pk=category_id)
        
        # Should not be able to extend twice the subscription
        helper = SubscriptionDurationHelper(category, request.user.profile.subscription)
        if (helper.end - helper.start).days >= category.duration * 2:
            return redirect('subscription-update-cancel')
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                    'price_data': {
                        'currency': settings.STRIPE_CURRENCY,
                        'unit_amount': category.price * 100, # stripe use cents
                        'product_data': {
                            'name': category.title,
                            'images': [
                                "https://www.fablab-chaux-de-fonds.ch/assets/fablab-logo-officiel-ddbeac0f8738a60507bd2441b7bc3bc9.svg"
                            ]
                        },
                    },
                    'quantity': 1,
                    },
                ],
                metadata = {
                    'profile_id': request.user.profile.id,
                    'subscription_category_id': category.id 
                },
                payment_method_types=['card'],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('subscription-update-success')),
                cancel_url=request.build_absolute_uri(reverse('subscription-update-cancel')),
                customer_email=request.user.email,
            )
        except Exception as e:
            return str(e)
        return redirect(checkout_session.url, code=303)

class CreateCheckoutSessionView(LoginRequiredMixin, ProfileRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Must have to confirm expected subscription category
        if 'category_id' not in kwargs:
            return redirect('subscription-update')

        session = StripeCheckoutSession()
        return session.create(request, kwargs['category_id'])
        

# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
  payload = request.body
  sig_header = request.META['HTTP_STRIPE_SIGNATURE']
  event = None

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)
  except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    return HttpResponse(status=400)

  # Handle the checkout.session.completed event
  if event['type'] == 'checkout.session.completed':
    session = event['data']['object']

    # Fulfill the purchase...
    fulfill_order(session, request)

  # Passed signature verification
  return HttpResponse(status=200)



def fulfill_order(session, request):
    customer_email = session['customer_details']['email']
    metadata = session['metadata']
    profile = Profile.objects.get(pk=metadata['profile_id'])
    subscription_category = SubscriptionCategory.objects.get(pk=metadata['subscription_category_id'])
    helper = SubscriptionDurationHelper(subscription_category, profile.subscription)
    subscription = Subscription.objects.create(
        start = helper.start,
        end = helper.end,
        subscription_category = subscription_category,
        access_number = profile.subscription.access_number if profile.subscription is not None else subscription_category.default_access_number
    )
    profile.subscription = subscription
    profile.save()

    context = {
        'profile': profile,
        'DOMAIN': Site.objects.first().domain,
        'date': format_datetime(helper.end, "d MMMM y", locale=settings.LANGUAGE_CODE),
    }

    context.update({
        'email_body': \
            mark_safe(_('Your subscription has been updated successfully until %(date)s<br>You can continue to use the fablab with premium prices') % context)
        }
    )

    html_message = render_to_string('accounts/email/subscription_updated.html', context)
    send_mail(
        subject=_("Your subsription has been updated successfully"),
        message="Your subsription has been updated successfully",
        from_email = None,
        recipient_list=[customer_email],
        html_message=html_message
    )
