from django.urls import include, path
from . import views

urlpatterns =[
    path('', include('django_registration.backends.activation.urls')),
    path('', include('django.contrib.auth.urls')),
    path('profile/', views.AccountsView, name='profile'),
    path('profile/edit/', views.EditProfileView, name='edit-profile'),
    path('profile/delete/', views.DeleteProfileView, name='delete-profile'),
    path("profile/subscription-management/<int:organization_pk>/people/<int:user_pk>/delete/", views.OrganizationUserDeleteView.as_view(), name="delete-organization-user"),
    path("profile/subscription-management/<int:organization_pk>/people/add/", views.OrganizationUserCreateView.as_view(), name="organization_user_add"),
    path('profile/subscription-management/', include('organizations.urls'), name='subscription-management'),
    path('invitations/token-error', views.token_error_view, name='invitations-token-error')
]
