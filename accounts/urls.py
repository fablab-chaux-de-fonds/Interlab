from django.urls import include, path
from . import views
from django.contrib.auth.views import PasswordResetConfirmView

urlpatterns =[
    path('register/', views.CustomRegistrationView.as_view(), name='django_registration_register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('', include('django_registration.backends.activation.urls')),
    path('', include('django.contrib.auth.urls')),
    path('activate/<str:activation_key>/', views.CustomActivationView.as_view(), name='django_registration_activate'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='auth_password_reset_confirm'),
    path('profile/', views.AccountsView, name='profile'),
    path('profile/edit/', views.EditProfileView, name='edit-profile'),
    path('profile/delete/', views.DeleteProfileView, name='delete-profile'),
    path("profile/subscription-management/<int:organization_pk>/people/<int:user_pk>/delete/", views.OrganizationUserDeleteView.as_view(), name="delete-organization-user"),
    path("profile/subscription-management/<int:organization_pk>/people/add/", views.OrganizationUserCreateView.as_view(), name="organization_user_add"),
    path('profile/subscription-management/', include('organizations.urls'), name='subscription-management'),
    path('invitations/token-error', views.token_error_view, name='invitations-token-error'),
    path('user-list', views.UserListView.as_view(template_name='accounts/user-list.html'), name='user-list'),
    path('user-list-filtered', views.UserListView.as_view(template_name='accounts/user-list-filtered.html'), name='user-list-filtered'),
    path('superuser-profile-edit/<int:pk>', views.SuperuserProfileEditView.as_view(), name='superuser-profile-edit')
]
