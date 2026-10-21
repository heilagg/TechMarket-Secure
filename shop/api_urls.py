from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.login_view, name='api-login'),
    path('auth/logout/', views.logout_view, name='api-logout'),
    path('orders/', views.OrderListCreateView.as_view(), name='order-list-create'),
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin-orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
]
