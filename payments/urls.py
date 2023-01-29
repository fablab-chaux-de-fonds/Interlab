from django.urls import include, path
from . import views

urlpatterns =[
    path('subscription-update/', views.SubscriptionUpdateView.as_view(), name='subscription-update'),
    path('subscription-update-success/', views.SubscriptionUpdateSuccessView.as_view(), name='subscription-update-success'),
    path('subscription-update-cancel/', views.SubscriptionUpdateCancelView.as_view(), name='subscription-update-cancel'),
    path('create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session' ),
    path('create-checkout-session/<int:category>/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session-category' ),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
    path('config/', views.stripe_config),
]