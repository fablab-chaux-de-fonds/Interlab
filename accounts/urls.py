from django.urls import include, path
from . import views
from django.contrib.auth.views import PasswordResetConfirmView

urlpatterns =[
    path('register/', views.CustomRegistrationView.as_view(), name='django_registration_register'),
    path('', include('django_registration.backends.activation.urls')),
    path('', include('django.contrib.auth.urls')),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='auth_password_reset_confirm'),
    path('profile/', views.AccountsView, name='profile'),
    path('profile/edit/', views.EditProfileView, name='edit-profile'),
    path('profile/delete/', views.DeleteProfileView, name='delete-profile'),
    path("profile/subscription-management/<int:organization_pk>/people/<int:user_pk>/delete/", views.OrganizationUserDeleteView.as_view(), name="delete-organization-user"),
    path("profile/subscription-management/<int:organization_pk>/people/add/", views.OrganizationUserCreateView.as_view(), name="organization_user_add"),
    path('profile/subscription-management/', include('organizations.urls'), name='subscription-management'),
    path('invitations/token-error', views.token_error_view, name='invitations-token-error'),
    path('user-list', views.user_list, name='user-list'),
    path('user-list-filtered', views.user_list_filtered, name='user-list-filtered'),
    path('user-edit/<int:user_pk>', views.user_edit, name='user-edit')
]
