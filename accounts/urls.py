from django.urls import path
from . import views

urlpatterns =[
    path('profile/', views.AccountsView, name='accounts'),
    path('profile/subscription-management/', include('organizations.urls')),
]
    