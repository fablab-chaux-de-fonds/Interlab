from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView
from . import views

admin.autodiscover()

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": {"cmspages": CMSSitemap}}),
]

urlpatterns += [
    path("admin/", admin.site.urls),
    path("accounts/", include('django.contrib.auth.urls')),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path('bootstrap/', views.bootstrap, name='bootstrap'),
    path("", include("cms.urls")),
]

# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
