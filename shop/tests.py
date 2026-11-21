"""Security regression tests. They run in CI on every pull request."""
import os
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from techmarket_project.settings import secret

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


class SecretProvisioningTests(SimpleTestCase):
    """Secrets can come from NAME_FILE (file provisioning) or NAME (env provisioning)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "demo_secret"
        self.path.write_text("value-from-file\n", encoding="utf-8")
        self.path.chmod(0o600)

    def test_reads_secret_from_file(self):
        with mock.patch.dict(os.environ, {"DEMO_SECRET_FILE": str(self.path)}, clear=False):
            os.environ.pop("DEMO_SECRET", None)
            self.assertEqual(secret("DEMO_SECRET"), "value-from-file")

    def test_reads_secret_from_env(self):
        with mock.patch.dict(os.environ, {"DEMO_SECRET": "value-from-env"}, clear=False):
            os.environ.pop("DEMO_SECRET_FILE", None)
            self.assertEqual(secret("DEMO_SECRET"), "value-from-env")

    def test_both_sources_is_a_configuration_error(self):
        env = {"DEMO_SECRET": "a", "DEMO_SECRET_FILE": str(self.path)}
        with mock.patch.dict(os.environ, env, clear=False), self.assertRaises(ImproperlyConfigured):
            secret("DEMO_SECRET")

    def test_missing_required_secret_fails_closed(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DEMO_SECRET", None)
            os.environ.pop("DEMO_SECRET_FILE", None)
            with self.assertRaises(ImproperlyConfigured):
                secret("DEMO_SECRET", required=True)

    def test_world_readable_secret_file_warns(self):
        self.path.chmod(0o644)
        with mock.patch.dict(os.environ, {"DEMO_SECRET_FILE": str(self.path)}, clear=False):
            os.environ.pop("DEMO_SECRET", None)
            with self.assertWarns(UserWarning):
                secret("DEMO_SECRET")

    def test_jwt_signing_key_is_configured(self):
        self.assertTrue(settings.SIMPLE_JWT["SIGNING_KEY"])
