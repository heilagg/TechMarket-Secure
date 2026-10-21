from django.contrib import admin
from django.urls import path, include
from shop.views import not_found
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('shop.api_urls')),
    path('', include('shop.urls')),
]

handler404 = not_found
