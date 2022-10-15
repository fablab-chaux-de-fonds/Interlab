from django.urls import path

from . import views

app_name = 'machines'

urlpatterns = [
    path('trainings/<int:pk>/show', views.training_show, name='trainings-show'),
    path('machines/<int:pk>/show', views.training_show, name='machines-show'),
]
