from django.urls import path

from . import views

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('create', views.PostCreateView.as_view(), name='post_create'),
    path('delete/<int:pk>', views.PostDeleteView.as_view(), name='post_delete'),
    path('update/<int:pk>', views.PostUpdateView.as_view(), name='post_update'),
]