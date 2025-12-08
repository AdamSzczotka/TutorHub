"""URL configuration for napiatke project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('panel/', include('apps.admin_panel.urls')),
    path('panel/subjects/', include('apps.subjects.urls')),
    path('panel/rooms/', include('apps.rooms.urls')),
    path('panel/lessons/', include('apps.lessons.urls')),
    path('panel/attendance/', include('apps.attendance.urls')),
    path('panel/messages/', include('apps.messages.urls')),
    path('panel/notifications/', include('apps.notifications.urls')),
    path('panel/', include('apps.core.urls')),
    path('', include('apps.landing.urls')),
]

# Development-only URLs
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
