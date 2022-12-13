from django.urls import path

from . import views

app_name = 'machines'

urlpatterns = [
    path('trainings/<int:pk>/show', views.training_show, name='trainings-show'),
    path('trainings/<int:pk>/validation/', views.TrainingValidation.as_view(), name='training-validation'),
    path('trainings/<int:pk>/waiting-list/', views.training_waiting_list, name='training-waiting-list'),
    path('machines/<int:pk>/show', views.MachineShowView.as_view(), name='machines-show'),
    path('machine/<int:pk>/slot', views.MachineSlotView.as_view(), name='machines-slot')
]