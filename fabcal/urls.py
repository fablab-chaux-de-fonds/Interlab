from django.urls import path
from . import views

urlpatterns = [
    path('create-opening/<str:start>/<str:end>/', views.CreateOpeningView.as_view(), name='create-opening'),
    path('update-opening/<int:pk>/', views.UpdateOpeningView.as_view(), name='update-opening'),
    path('delete-opening/<int:pk>/', views.DeleteOpeningView.as_view(), name='delete-opening'),
    path('download-ics-file/<str:summary>/<str:start>/<str:end>/', views.downloadIcsFileView.as_view(), name='download-ics-file'),
    path('create-event/<str:start>/<str:end>/', views.CreateEventView.as_view(), name='create-event'),
    path('update-event/<int:pk>/', views.UpdateEventView.as_view(), name='update-event'),
    path('delete-event/<int:pk>/', views.DeleteEventView.as_view(), name='delete-event'),
    path('event/<int:pk>/', views.DetailEventView.as_view(), name='show-event'),
    path('register-event/<int:pk>/', views.RegisterEventView.as_view(), name='register-event'),
    path('unregister-event/<int:pk>/', views.UnregisterEventView.as_view(), name='unregister-event'),
    path('create-training/<str:start>/<str:end>/', views.CreateTrainingView.as_view(), name='create-training'),
    path('update-training/<int:pk>/', views.UpdateTrainingView.as_view(), name='update-training'),
    path('delete-training/<int:pk>/', views.DeleteTrainingView.as_view(), name='delete-training'),  
]