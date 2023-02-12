from django.urls import path
from . import views

app_name = 'fabcal'

urlpatterns = [
    path('create-opening/<str:start>/<str:end>/', views.CreateOpeningView.as_view(), name='create-opening'),
    path('update-opening/<int:pk>/', views.UpdateOpeningView.as_view(), name='update-opening'),
    path('delete-opening/<int:pk>/', views.DeleteOpeningView.as_view(), name='delete-opening'),
    path('download-ics-file/<str:summary>/<str:start>/<str:end>/', views.downloadIcsFileView.as_view(), name='download-ics-file'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('event/add/<str:start>/<str:end>/', views.EventCreateView.as_view(), name='event-add'),
    path('event/<int:pk>/update', views.EventUpdateView.as_view(), name='event-update'),
    path('event/<int:pk>/delete', views.EventDeleteView.as_view(), name='event-delete'),
    path('event/<int:pk>/register', views.EventRegisterView.as_view(), name='event-register'),
    path('event/<int:pk>/unregister', views.UnregisterEventView.as_view(), name='event-unregister'),
    path('create-training/<str:start>/<str:end>/', views.CreateTrainingView.as_view(), name='create-training'),
    path('update-training/<int:pk>/', views.UpdateTrainingView.as_view(), name='update-training'),
    path('delete-training/<int:pk>/', views.DeleteTrainingView.as_view(), name='delete-training'),  
    path('register-training/<int:pk>/', views.RegisterTrainingView.as_view(), name='register-training'),
    path('unregister-training/<int:pk>/', views.UnregisterTrainingView.as_view(), name='unregister-training'),
    path('machine/reservation/<int:pk>/', views.CreateMachineReservationView.as_view(), name='machine-reservation'),
    path('machine/reservation/<int:pk>/update/', views.UpdateMachineReservationView.as_view(), name='machine-reservation-update'),
    path('machine/reservation/<int:pk>/delete/', views.DeleteMachineReservationView.as_view(), name='machine-reservation-delete'),
]