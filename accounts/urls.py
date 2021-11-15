from django.urls import path
from . import views

urlpatterns =[
    path('profile/', views.AccountsView, name='accounts'),
    path('profile/edit/', views.EditProfileView, name='edit profile'),
    path('profile/delete/', views.DeleteProfileView, name='delete profile')
]
    