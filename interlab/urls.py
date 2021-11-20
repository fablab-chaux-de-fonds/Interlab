from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
from . import views
import debug_toolbar

admin.autodiscover()

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": {"cmspages": CMSSitemap}}),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path(r'^invitations/', include('invitations.urls', namespace='invitations')),
    path('bootstrap/', views.bootstrap, name='bootstrap'),
    path("", include("cms.urls")),
    prefix_default_language=False
)

# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    import debug_toolbar
    urlpatterns += i18n_patterns(
       path(r'^__debug__/', include(debug_toolbar.urls)),
       prefix_default_language=False
    )

