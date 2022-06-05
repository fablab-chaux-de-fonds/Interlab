from django.urls import include, path, re_path
from . import views

urlpatterns = [
    path('create-opening/<str:start>/<str:end>/', views.CreateOpeningView.as_view(), name='create-opening'),
]