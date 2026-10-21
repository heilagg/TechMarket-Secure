"""Security regression tests. They run in CI on every pull request."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Brand, Category, Order, Phone

PASSWORD = "Str0ng!Passw0rd"


class OrderApiSecurityTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="TestBrand")
        category = Category.objects.create(name="Phones")
        self.phone = Phone.objects.create(name="X1", brand=brand, category=category, price="100.00")
        self.alice = User.objects.create_user("alice", password=PASSWORD)
        self.bob = User.objects.create_user("bob", password=PASSWORD)
        self.admin = User.objects.create_user("shopadmin", password=PASSWORD, is_staff=True)
        self.alice_order = Order.objects.create(user=self.alice, phone=self.phone, quantity=1)
        self.client = APIClient()

    def auth(self, user):
        access = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    # --- Authentication (JWT) ---
    def test_orders_require_authentication(self):
        self.assertEqual(self.client.get("/api/orders/").status_code, 401)

    def test_jwt_login_returns_access_and_refresh_tokens(self):
        response = self.client.post("/api/token/", {"username": "alice", "password": PASSWORD}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_jwt_login_with_wrong_password_is_rejected(self):
        response = self.client.post("/api/token/", {"username": "alice", "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("access", response.json())

    def test_access_token_is_short_lived(self):
        self.assertLessEqual(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"], timedelta(minutes=15))

    def test_old_non_expiring_drf_token_is_not_accepted(self):
        token, _ = Token.objects.get_or_create(user=self.alice)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        self.assertEqual(self.client.get("/api/orders/").status_code, 401)

    def test_passwords_are_hashed_with_argon2id(self):
        self.assertTrue(self.alice.password.startswith("argon2$argon2id$"))

    # --- Authorization: object ownership (IDOR) ---
    def test_user_sees_only_own_orders(self):
        self.auth(self.bob)
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_idor_other_users_order_is_not_accessible(self):
        self.auth(self.bob)
        url = f"/api/orders/{self.alice_order.id}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.put(url, {"quantity": 2}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertTrue(Order.objects.filter(pk=self.alice_order.pk).exists())

    def test_order_owner_cannot_be_spoofed(self):
        self.auth(self.bob)
        response = self.client.post(
            "/api/orders/", {"phone": self.phone.id, "quantity": 1, "user": self.alice.id}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.get(pk=response.json()["id"]).user, self.bob)

    # --- Authorization: roles (admin endpoint) ---
    def test_admin_orders_requires_login(self):
        self.assertEqual(self.client.get("/api/admin/orders/").status_code, 401)

    def test_admin_orders_forbidden_for_customer(self):
        self.auth(self.alice)
        self.assertEqual(self.client.get("/api/admin/orders/").status_code, 403)

    def test_admin_orders_allowed_for_admin(self):
        self.auth(self.admin)
        response = self.client.get("/api/admin/orders/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    # --- Business logic (fixed by PR #3, kept as regression tests) ---
    def test_customer_cannot_change_order_status(self):
        self.auth(self.alice)
        self.client.put(f"/api/orders/{self.alice_order.id}/", {"status": "delivered"}, format="json")
        self.alice_order.refresh_from_db()
        self.assertEqual(self.alice_order.status, "pending")

    def test_zero_quantity_order_is_rejected(self):
        self.auth(self.alice)
        response = self.client.post("/api/orders/", {"phone": self.phone.id, "quantity": 0}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_quantity_above_stock_is_rejected(self):
        self.auth(self.alice)
        response = self.client.post(
            "/api/orders/", {"phone": self.phone.id, "quantity": self.phone.stock + 1}, format="json"
        )
        self.assertEqual(response.status_code, 400)
