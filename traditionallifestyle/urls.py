"""
URL configuration for traditionallifestyle project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core app (landing, home, brand selection)
    path('', include('apps.core.urls')),

    # Authentication (django-allauth)
    path('accounts/', include('allauth.urls')),

    # App-specific URLs
    path('user/', include('apps.accounts.urls')),
    path('booking/', include('apps.booking.urls')),
    path('membership/', include('apps.membership.urls')),
    path('shop/', include('apps.shop.urls')),
    path('blog/', include('apps.blog.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
