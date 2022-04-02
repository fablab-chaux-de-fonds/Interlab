from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
from . import views

from organizations.backends import invitation_backend

admin.autodiscover()

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": {"cmspages": CMSSitemap}}),
]

# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    import debug_toolbar
    urlpatterns += i18n_patterns(
       path('__debug__/', include('debug_toolbar.urls')),
       prefix_default_language=False
    )

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('invitations/', include(invitation_backend().get_urls())),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path('bootstrap/', views.bootstrap, name='bootstrap'),
    path('schedule/', views.schedule, name='schedule'),
    path("", include("newsletter.urls")),
    path("", include("cms.urls")),
    prefix_default_language=False
)

