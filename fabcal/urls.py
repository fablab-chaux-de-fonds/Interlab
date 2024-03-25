from django.urls import path
from . import views

app_name = 'fabcal'

urlpatterns = [
    path('openingslot/create/<str:start>/<str:end>/', views.OpeningSlotCreateView.as_view(), name='openingslot-create'), 
    path('openingslot/update/<int:pk>/', views.OpeningSlotUpdateView.as_view(), name='openingslot-update'),
    path('openingslot/delete/<int:pk>/', views.OpeningSlotDeleteView.as_view(), name='openingslot-delete'),
    path('machineslot/update/<int:pk>/', views.MachineSlotUpdateView.as_view(), name='machineslot-update'),
    path('machineslot/delete/<int:pk>/', views.MachineSlotDeleteView.as_view(), name='machineslot-delete'),
    path('trainingslot/create/<str:start>/<str:end>/', views.TrainingSlotCreateView.as_view(), name='trainingslot-create'),
    path('trainingslot/update/<int:pk>/', views.TrainingSlotUpdateView.as_view(), name='trainingslot-update'),
    path('trainingslot/delete/<int:pk>/', views.TrainingSlotDeleteView.as_view(), name='trainingslot-delete'),
    path('trainingslot/register/create/<int:pk>', views.TrainingSlotRegistrationCreateView.as_view(), name='trainingslot-register'),
    path('trainingslot/register/delete/<int:pk>', views.TrainingSlotRegistrationDeleteView.as_view(), name='trainingslot-unregister'),
    path('download-ics-file/<str:summary>/<str:start>/<str:end>/', views.downloadIcsFileView.as_view(), name='download-ics-file'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('event/add/<str:start>/<str:end>/', views.EventCreateView.as_view(), name='event-add'),
    path('event/<int:pk>/update', views.EventUpdateView.as_view(), name='event-update'),
    path('event/<int:pk>/delete', views.EventDeleteView.as_view(), name='event-delete'),
    path('event/<int:pk>/register', views.EventRegisterView.as_view(), name='event-register'),
    path('event/<int:pk>/unregister', views.EventUnregisterView.as_view(), name='event-unregister'),
    path('training/<int:pk>/unregister', views.TrainingUnregisterView.as_view(), name='training-unregister'),
    path('machine/reservation/future/', views.MachineFutureReservationListView.as_view(), name='machine-reservation-future'),
    path('machine/reservation/past/', views.MachinePastReservationListView.as_view(), name='machine-reservation-past')
]