from django.db import models
from django.contrib.auth.models import User


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return self.name


class PhoneManager(models.Manager):
    def in_stock(self):
        return self.filter(in_stock=True)


class Phone(models.Model):
    name = models.CharField(max_length=200)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='phones')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='phones')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    memory_gb = models.PositiveIntegerField(default=64)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=220, blank=True)
    specifications = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.7)
    stock = models.PositiveIntegerField(default=12)
    sold_count = models.PositiveIntegerField(default=0)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PhoneManager()

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    @property
    def display_image(self):
        return self.image or 'shop/img/product-default.svg'

    @property
    def stock_label(self):
        if not self.in_stock or self.stock == 0:
            return 'Out of stock'
        if self.stock <= 3:
            return 'Few left'
        return 'In stock'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class CustomerProfile(models.Model):
    REWARD_CHOICES = [
        ('', 'No reward'),
        ('discount', '10% Discount Coupon'),
        ('shipping', 'Free Shipping'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    wheel_used = models.BooleanField(default=False)
    reward_type = models.CharField(max_length=20, choices=REWARD_CHOICES, blank=True)
    coupon_code = models.CharField(max_length=24, blank=True)
    free_shipping = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} profile"
