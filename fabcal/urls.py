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
    path('trainingslot/register/create/<int:pk>/', views.TrainingSlotRegistrationCreateView.as_view(), name='trainingslot-register'),
    path('trainingslot/register/delete/<int:pk>/', views.TrainingSlotRegistrationDeleteView.as_view(), name='trainingslot-unregister'),
    path('eventslot/<int:pk>/', views.EventDetailView.as_view(), name='eventslot-detail'),
    path('eventslot/create/<str:start>/<str:end>/', views.EventSlotCreateView.as_view(), name='eventslot-create'),
    path('eventslot/update/<int:pk>/', views.EventSlotUpdateView.as_view(), name='eventslot-update'),
    path('eventslot/delete/<int:pk>/', views.EventSlotDeleteView.as_view(), name='eventslot-delete'),
    path('eventslot/register/create/<int:pk>/', views.EventSlotRegistrationCreateView.as_view(), name='eventslot-register'),
    path('eventslot/register/delete/<int:pk>/', views.EventSlotRegistrationDeleteView.as_view(), name='eventslot-unregister'),
    path('download-ics-file/<str:summary>/<str:start>/<str:end>/', views.downloadIcsFileView.as_view(), name='download-ics-file'),
    path('machine/reservation/future/', views.MachineFutureReservationListView.as_view(), name='machine-reservation-future'),
    path('machine/reservation/past/', views.MachinePastReservationListView.as_view(), name='machine-reservation-past')
]