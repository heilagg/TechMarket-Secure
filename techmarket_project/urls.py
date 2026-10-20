from django.contrib import admin
from django.urls import path, include
from shop.views import not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('shop.api_urls')),
    path('', include('shop.urls')),
]

handler404 = not_found
