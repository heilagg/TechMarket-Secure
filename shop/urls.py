from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('categories/', views.categories, name='categories'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_page, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.orders, name='orders'),
    path('wheel/spin/', views.spin_lucky_wheel, name='spin_lucky_wheel'),
    path('wheel/dismiss/', views.dismiss_lucky_wheel, name='dismiss_lucky_wheel'),
]
