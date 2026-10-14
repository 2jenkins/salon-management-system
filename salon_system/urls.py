from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'Luxe Salon Administration'
admin.site.site_title = 'Luxe Salon Admin'
admin.site.index_title = 'Salon management'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('salon_services.urls')),
    path('accounts/', include('accounts.urls')),
    path('appointments/', include('bookings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
