import stripe
import datetime

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.http.response import JsonResponse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView

from accounts.models import Subscription

class SubscriptionUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "payments/subscription_update.html"

class SubscriptionUpdateSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "payments/subscription_update_success.html"

class SubscriptionUpdateCancelView(LoginRequiredMixin, TemplateView):
    template_name = "payments/subscription_update_cancel.html"

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)

class CreateCheckoutSessionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        YOUR_DOMAIN =  request.scheme + '://' + Site.objects.get_current().domain + '/'
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                    'price_data': {
                        'currency': settings.STRIPE_CURRENCY,
                        'unit_amount': request.user.profile.subscription.subscription_category.price * 100, # stripe use cents
                        'product_data': {
                            'name': request.user.profile.subscription.subscription_category.title,
                            'images': [
                                "https://www.fablab-chaux-de-fonds.ch/assets/fablab-logo-officiel-ddbeac0f8738a60507bd2441b7bc3bc9.svg"
                            ]
                        },
                    },
                    'quantity': 1,
                    },
                ],
                payment_method_types=['card'],
                mode='payment',
                success_url=YOUR_DOMAIN + 'payments/subscription-update-success/',
                cancel_url=YOUR_DOMAIN + 'payments/subscription-update-cancel/',
                customer_email=request.user.email,
            )
        except Exception as e:
            return str(e)
        return redirect(checkout_session.url, code=303)


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        #TODO test on hidora
        Subscription.objects.filter(pk=request.user.profile.subscription.id).update(
            end=datetime.datetime.now() + 
            datetime.timedelta(days=request.user.profile.subscription.subscription_category.duration)
            )
    return HttpResponse(status=200)