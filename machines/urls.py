from django.urls import path

from . import views

app_name = 'machines'

urlpatterns = [
    path('trainings', views.trainings_list, name='trainings.list'),
    path('trainings/<int:pk>/show', views.training_show, name='trainings.show'),
]
