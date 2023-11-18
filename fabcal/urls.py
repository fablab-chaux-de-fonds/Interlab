from django.urls import path
from . import views

app_name = 'fabcal'

urlpatterns = [
    path('openingslot/create/', views.OpeningSlotCreateView.as_view(), name='openingslot-create'), 
    path('openingslot/update/<int:pk>/', views.OpeningSlotUpdateView.as_view(), name='openingslot-update'),
    path('openingslot/delete/<int:pk>/', views.OpeningSlotDeleteView.as_view(), name='openingslot-delete'),
    path('download-ics-file/<str:summary>/<str:start>/<str:end>/', views.downloadIcsFileView.as_view(), name='download-ics-file'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('event/add/<str:start>/<str:end>/', views.EventCreateView.as_view(), name='event-add'),
    path('event/<int:pk>/update', views.EventUpdateView.as_view(), name='event-update'),
    path('event/<int:pk>/delete', views.EventDeleteView.as_view(), name='event-delete'),
    path('event/<int:pk>/register', views.EventRegisterView.as_view(), name='event-register'),
    path('event/<int:pk>/unregister', views.EventUnregisterView.as_view(), name='event-unregister'),
    path('training/add/<str:start>/<str:end>/', views.TrainingCreateView.as_view(), name='training-add'),
    path('training/<int:pk>/update', views.TrainingUpdateView.as_view(), name='training-update'),
    path('training/<int:pk>/delete', views.TrainingDeleteView.as_view(), name='training-delete'),  
    path('training/<int:pk>/register', views.TrainingRegisterView.as_view(), name='training-register'),
    path('training/<int:pk>/unregister', views.TrainingUnregisterView.as_view(), name='training-unregister'),
    path('machineslot/update/<int:pk>/', views.MachineSlotUpdateView.as_view(), name='machineslot-update'),
    path('machine/reservation/<int:pk>/update/', views.UpdateMachineReservationView.as_view(), name='machine-reservation-update'),
    path('machine/reservation/<int:pk>/delete/', views.DeleteMachineReservationView.as_view(), name='machine-reservation-delete'),
    path('machine/reservation/future/', views.MachineFutureReservationListView.as_view(), name='machine-reservation-future'),
    path('machine/reservation/past/', views.MachinePastReservationListView.as_view(), name='machine-reservation-past')
]