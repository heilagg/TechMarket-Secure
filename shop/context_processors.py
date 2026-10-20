from .models import Category


def storefront_context(request):
    cart = request.session.get('cart', {})
    return {
        'global_categories': Category.objects.order_by('name'),
        'cart_item_count': sum(cart.values()) if isinstance(cart, dict) else 0,
    }
