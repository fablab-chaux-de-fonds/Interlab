from django.urls import include, path, re_path
from . import views

urlpatterns = [
    path('create-opening/<str:start>/<str:end>/', views.CreateOpeningView.as_view(), name='create-opening'),
    path('update-opening/<int:pk>/', views.UpdateOpeningView.as_view(), name='update-opening'),
    path('download-ics-file/<str:summary>/<str:start>/<str:end>/', views.downloadIcsFileView.as_view(), name='download-ics-file')
]