from django.urls import path
from . import views

app_name = 'fabcal'

urlpatterns = [
    path('create-opening/<str:start>/<str:end>/', views.CreateOpeningView.as_view(), name='create-opening'),
    path('update-opening/<int:pk>/', views.UpdateOpeningView.as_view(), name='update-opening'),
    path('opening/<int:pk>/delete', views.OpeningSlotDeleteView.as_view(), name='opening-delete'),
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
    path('machine/reservation/<int:pk>/', views.CreateMachineReservationView.as_view(), name='machine-reservation'),
    path('machine/reservation/<int:pk>/update/', views.UpdateMachineReservationView.as_view(), name='machine-reservation-update'),
    path('machine/reservation/<int:pk>/delete/', views.DeleteMachineReservationView.as_view(), name='machine-reservation-delete'),
]