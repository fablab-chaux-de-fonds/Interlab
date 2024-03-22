from django.urls import re_path
from . import views

urlpatterns = [
    re_path('(?P<version>(v1))/opening/', views.OpeningSet.as_view()),
    re_path('(?P<version>(v1))/opening_slot/', views.OpeningSlotSet.as_view()),
    re_path('(?P<version>(v1))/machine_slot/', views.MachineSlotSet.as_view()),
    re_path('(?P<version>(v1))/custom_user/', views.CustomUserSet.as_view()),
    re_path('(?P<version>(v1))/subscription/', views.SubscriptionSet.as_view()),
    re_path('(?P<version>(v1))/profile/', views.ProfileSet.as_view()),
]