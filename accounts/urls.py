from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns =[
    path('profile/', views.AccountsView, name='accounts'),
    path('profile/edit/', views.EditProfileView, name='edit profile')
]
    