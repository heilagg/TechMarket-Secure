from rest_framework import serializers
from .models import Brand, Category, Phone, Order

class BrandSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100, allow_blank=True, required=False)

    def create(self, validated_data):
        return Brand.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.country = validated_data.get('country', instance.country)
        instance.save()
        return instance


class CategorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(allow_blank=True, required=False)
    icon = serializers.CharField(max_length=40, allow_blank=True, required=False)

    def create(self, validated_data):
        return Category.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.icon = validated_data.get('icon', instance.icon)
        instance.save()
        return instance

class PhoneSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Phone
        fields = [
            'id', 'brand', 'brand_name', 'category', 'category_name',
            'name', 'price', 'old_price', 'memory_gb', 'description',
            'short_description', 'specifications', 'image', 'rating',
            'stock', 'sold_count', 'in_stock', 'created_at',
        ]


MAX_ORDER_QUANTITY = 10


class OrderSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    phone_name = serializers.CharField(source='phone.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'username', 'phone', 'phone_name',
            'quantity', 'status', 'created_at',
        ]
        # status is set by staff/the system, never by the customer
        read_only_fields = ['id', 'user', 'status', 'created_at']

    def validate_quantity(self, value):
        if value < 1 or value > MAX_ORDER_QUANTITY:
            raise serializers.ValidationError(f'Quantity must be between 1 and {MAX_ORDER_QUANTITY}.')
        return value

    def validate(self, attrs):
        if self.instance is not None:
            if self.instance.status != 'pending':
                raise serializers.ValidationError('Only pending orders can be modified.')
            if 'phone' in attrs and attrs['phone'] != self.instance.phone:
                raise serializers.ValidationError({'phone': 'The product of an order cannot be changed.'})
        phone = attrs.get('phone') or (self.instance.phone if self.instance else None)
        quantity = attrs.get('quantity', self.instance.quantity if self.instance else 1)
        if phone is not None and (not phone.in_stock or quantity > phone.stock):
            raise serializers.ValidationError('Not enough stock for this product.')
        return attrs
