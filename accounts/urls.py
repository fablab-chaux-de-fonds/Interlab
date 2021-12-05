from django.urls import include, path
from . import views

urlpatterns =[
    path('profile/', views.AccountsView, name='profile'),
    path('profile/edit/', views.EditProfileView, name='edit-profile'),
    path('profile/delete/', views.DeleteProfileView, name='delete-profile'),
    path("profile/subscription-management/<int:organization_pk>/people/<int:user_pk>/delete/", views.DeleteOrganizationUserView, name="delete-organization-user"),
    path('profile/subscription-management/', include('organizations.urls'), name='subscription-management'),
]
