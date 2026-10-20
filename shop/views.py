import random
import string
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Max, Min, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import Brand, Category, CustomerProfile, Order, Phone
from .serializers import OrderSerializer


def _cart(request):
    return request.session.setdefault('cart', {})


def _cart_items(cart):
    ids = [int(pk) for pk in cart.keys()]
    phones = Phone.objects.filter(id__in=ids).select_related('brand', 'category')
    items = []
    total = Decimal('0.00')
    for phone in phones:
        quantity = int(cart.get(str(phone.id), 0))
        line_total = phone.price * quantity
        total += line_total
        items.append({'phone': phone, 'quantity': quantity, 'line_total': line_total})
    return items, total


def _money(value):
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _generate_coupon(prefix):
    return prefix + '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _checkout_totals(request, subtotal):
    profile_obj, _ = CustomerProfile.objects.get_or_create(user=request.user)
    entered_code = request.session.get('applied_promo_code', '')
    applied_reward = ''
    promo_message = ''

    delivery = _money(subtotal * Decimal('0.10'))
    discount = Decimal('0.00')

    if entered_code:
        if profile_obj.coupon_code and entered_code.upper() == profile_obj.coupon_code.upper():
            applied_reward = profile_obj.reward_type
            if profile_obj.reward_type == 'discount':
                discount = _money(subtotal * Decimal('0.10'))
                promo_message = '10% discount applied.'
            elif profile_obj.reward_type == 'shipping':
                delivery = Decimal('0.00')
                promo_message = 'Free shipping applied.'
        else:
            promo_message = 'Promo code was not found for your account.'

    grand_total = _money(subtotal - discount + delivery)
    return {
        'profile': profile_obj,
        'promo_code': entered_code,
        'applied_reward': applied_reward,
        'promo_message': promo_message,
        'subtotal': _money(subtotal),
        'delivery': delivery,
        'discount': discount,
        'grand_total': grand_total,
    }


def _remember_product(request, phone_id):
    recent = request.session.get('recently_viewed', [])
    recent = [pk for pk in recent if pk != phone_id]
    recent.insert(0, phone_id)
    request.session['recently_viewed'] = recent[:6]


def home(request):
    phones = Phone.objects.select_related('brand', 'category')
    context = {
        'featured_products': phones.filter(in_stock=True).order_by('-rating', '-sold_count')[:8],
        'new_arrivals': phones.order_by('-created_at')[:8],
        'best_sellers': phones.order_by('-sold_count', '-rating')[:8],
        'categories': Category.objects.annotate(avg_rating=Avg('phones__rating')).order_by('name'),
        'brands': Brand.objects.order_by('name')[:10],
    }
    return render(request, 'shop/home.html', context)


def catalog(request):
    products = Phone.objects.select_related('brand', 'category').all()
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    brand = request.GET.get('brand', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', 'newest')

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(category__name__icontains=query)
            | Q(description__icontains=query)
        )
    if category:
        products = products.filter(category_id=category)
    if brand:
        products = products.filter(brand_id=brand)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    sort_map = {
        'price_asc': 'price',
        'price_desc': '-price',
        'alpha': 'name',
        'rating': '-rating',
        'newest': '-created_at',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    price_bounds = Phone.objects.aggregate(min_price=Min('price'), max_price=Max('price'))

    return render(request, 'shop/catalog.html', {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': Category.objects.order_by('name'),
        'brands': Brand.objects.order_by('name'),
        'price_bounds': price_bounds,
        'selected': {
            'q': query,
            'category': category,
            'brand': brand,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort,
        },
    })


def categories(request):
    return render(request, 'shop/categories.html', {
        'categories': Category.objects.prefetch_related('phones').order_by('name'),
    })


def product_detail(request, pk):
    phone = get_object_or_404(Phone.objects.select_related('brand', 'category'), pk=pk)
    _remember_product(request, phone.id)
    related = Phone.objects.filter(category=phone.category).exclude(pk=phone.pk).select_related('brand', 'category')[:4]
    recent_ids = request.session.get('recently_viewed', [])[1:]
    recent = Phone.objects.filter(id__in=recent_ids).select_related('brand', 'category')
    specs = [line.strip() for line in phone.specifications.splitlines() if line.strip()]
    return render(request, 'shop/product_detail.html', {
        'phone': phone,
        'related_products': related,
        'recently_viewed': recent,
        'specs': specs,
    })


@login_required
@require_POST
def add_to_cart(request, pk):
    phone = get_object_or_404(Phone, pk=pk, in_stock=True)
    cart = _cart(request)
    quantity = int(request.POST.get('quantity', 1))
    cart[str(phone.id)] = min(cart.get(str(phone.id), 0) + quantity, max(phone.stock, 1))
    request.session.modified = True
    messages.success(request, f'{phone.brand.name} {phone.name} added to cart.')
    return redirect(request.POST.get('next') or 'cart')


@login_required
@require_POST
def update_cart(request, pk):
    cart = _cart(request)
    quantity = int(request.POST.get('quantity', 0))
    if quantity <= 0:
        cart.pop(str(pk), None)
        messages.info(request, 'Item removed from cart.')
    else:
        phone = get_object_or_404(Phone, pk=pk)
        cart[str(pk)] = min(quantity, max(phone.stock, 1))
        messages.success(request, 'Cart updated.')
    request.session.modified = True
    return redirect('cart')


def cart(request):
    items, total = _cart_items(_cart(request))
    return render(request, 'shop/cart.html', {'cart_items': items, 'cart_total': total})


@login_required
def checkout(request):
    cart_data = _cart(request)
    items, total = _cart_items(cart_data)
    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    if request.method == 'POST':
        if 'apply_promo' in request.POST:
            promo_code = request.POST.get('promo_code', '').strip().upper()
            if promo_code:
                request.session['applied_promo_code'] = promo_code
                messages.info(request, 'Promo code checked.')
            else:
                request.session.pop('applied_promo_code', None)
                messages.info(request, 'Promo code removed.')
            return redirect('checkout')

        for item in items:
            Order.objects.create(user=request.user, phone=item['phone'], quantity=item['quantity'])
            item['phone'].sold_count += item['quantity']
            item['phone'].stock = max(item['phone'].stock - item['quantity'], 0)
            item['phone'].in_stock = item['phone'].stock > 0
            item['phone'].save(update_fields=['sold_count', 'stock', 'in_stock'])
        request.session['cart'] = {}
        request.session.pop('applied_promo_code', None)
        messages.success(request, 'Order placed successfully. We are preparing your tech.')
        return redirect('orders')
    totals = _checkout_totals(request, total)
    return render(request, 'shop/checkout.html', {'cart_items': items, 'cart_total': total, **totals})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            CustomerProfile.objects.get_or_create(user=user)
            login(request, user)
            request.session['show_lucky_wheel'] = True
            messages.success(request, 'Welcome to TechMarket. Spin your welcome reward.')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'shop/auth/register.html', {'form': form})


def login_page(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'You are signed in.')
            return redirect(request.GET.get('next') or 'home')
    else:
        form = LoginForm(request)
    return render(request, 'shop/auth/login.html', {'form': form})


def logout_page(request):
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('home')


@login_required
def profile(request):
    profile_obj, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    orders = Order.objects.filter(user=request.user).select_related('phone', 'phone__brand').order_by('-created_at')[:5]
    return render(request, 'shop/profile.html', {'form': form, 'profile': profile_obj, 'orders': orders})


@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).select_related('phone', 'phone__brand').order_by('-created_at')
    return render(request, 'shop/orders.html', {'orders': user_orders})


@login_required
@require_POST
def spin_lucky_wheel(request):
    profile_obj, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if profile_obj.wheel_used:
        return JsonResponse({'ok': False, 'message': 'Reward already claimed.'}, status=400)

    # Only these two rewards are selectable. Free iPhone and Nothing are visual-only wheel segments.
    reward = random.choices(['discount', 'shipping'], weights=[65, 35], k=1)[0]
    profile_obj.wheel_used = True
    if reward == 'discount':
        code = _generate_coupon('TECH10')
        profile_obj.reward_type = 'discount'
        profile_obj.coupon_code = code
        profile_obj.free_shipping = False
        message = f'You won 10% discount. Promo code: {code}'
    else:
        code = _generate_coupon('SHIPFREE')
        profile_obj.reward_type = 'shipping'
        profile_obj.coupon_code = code
        profile_obj.free_shipping = True
        message = f'You won free shipping. Promo code: {code}'
    profile_obj.save()
    request.session['show_lucky_wheel'] = False
    return JsonResponse({'ok': True, 'reward': reward, 'message': message})


def dismiss_lucky_wheel(request):
    request.session['show_lucky_wheel'] = False
    return JsonResponse({'ok': True})


def not_found(request, exception=None):
    return render(request, 'shop/404.html', status=404)


# ---------------------------------------------------------------------------
# Function-Based Views (DRF-декораторы) — Token-based authentication
# ---------------------------------------------------------------------------

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/auth/login/
    body: {"username": "...", "password": "..."}
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Необходимо указать username и password.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)
    if user is None:
        return Response(
            {'error': 'Неверный логин или пароль.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    POST /api/auth/logout/
    Требует заголовок: Authorization: Token <token>
    """
    try:
        request.user.auth_token.delete()
    except (AttributeError, Token.DoesNotExist):
        return Response(
            {'error': 'Активный токен не найден.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {'message': 'Вы успешно вышли из системы.'},
        status=status.HTTP_200_OK,
    )


# ---------------------------------------------------------------------------
# Class-Based Views (APIView) — Full CRUD для Order, привязанного к request.user
# ---------------------------------------------------------------------------

class OrderListCreateView(APIView):
    """
    GET  /api/orders/  — список заказов текущего пользователя
    POST /api/orders/  — создать новый заказ (привязывается к request.user)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    """
    GET    /api/orders/<pk>/  — получить один заказ
    PUT    /api/orders/<pk>/  — обновить заказ
    DELETE /api/orders/<pk>/  — удалить заказ
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(Order, pk=pk, user=user)

    def get(self, request, pk):
        order = self.get_object(pk, request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        order = self.get_object(pk, request.user)
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        order = self.get_object(pk, request.user)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
