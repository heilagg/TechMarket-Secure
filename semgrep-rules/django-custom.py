# Test file for semgrep-rules/django-custom.yml  (run: semgrep --test semgrep-rules/)
import random
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

# ruleid: techmarket-hardcoded-secret-key
SECRET_KEY = 'django-insecure-abc'
# ok: techmarket-hardcoded-secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)

# ruleid: techmarket-debug-true
DEBUG = True
# ok: techmarket-debug-true
DEBUG = env("DJANGO_DEBUG", "False").lower() == "true"

# ruleid: techmarket-cors-allow-all
CORS_ALLOW_ALL_ORIGINS = True

# ruleid: techmarket-insecure-random-for-codes
code = ''.join(random.choices("ABC", k=6))


# ruleid: techmarket-csrf-exempt
@csrf_exempt
def pay(request):
    pass


# ruleid: techmarket-drf-allowany
@permission_classes([AllowAny])
def login_view(request):
    pass


def order_detail(request, pk):
    # ruleid: techmarket-order-idor
    order = get_object_or_404(Order, pk=pk)
    # ok: techmarket-order-idor
    order = get_object_or_404(Order, pk=pk, user=request.user)
    # ruleid: techmarket-raw-sql
    Order.objects.raw(f"SELECT * FROM shop_order WHERE id = {pk}")
    # ruleid: techmarket-mark-safe
    return mark_safe(order.note)
