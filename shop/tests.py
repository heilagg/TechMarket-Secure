"""Security regression tests. They run in CI on every pull request."""
import unittest

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Brand, Category, Order, Phone


class OrderApiSecurityTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="TestBrand")
        category = Category.objects.create(name="Phones")
        self.phone = Phone.objects.create(name="X1", brand=brand, category=category, price="100.00")
        self.alice = User.objects.create_user("alice", password="Str0ng!Passw0rd")
        self.bob = User.objects.create_user("bob", password="Str0ng!Passw0rd")
        self.alice_order = Order.objects.create(user=self.alice, phone=self.phone, quantity=1)
        self.client = APIClient()

    def auth(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_orders_require_authentication(self):
        self.assertEqual(self.client.get("/api/orders/").status_code, 401)

    def test_user_sees_only_own_orders(self):
        self.auth(self.bob)
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_idor_other_users_order_is_not_accessible(self):
        self.auth(self.bob)
        url = f"/api/orders/{self.alice_order.id}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.put(url, {"quantity": 99}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertTrue(Order.objects.filter(pk=self.alice_order.pk).exists())

    def test_order_owner_cannot_be_spoofed(self):
        self.auth(self.bob)
        response = self.client.post(
            "/api/orders/", {"phone": self.phone.id, "quantity": 1, "user": self.alice.id}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.get(pk=response.json()["id"]).user, self.bob)

    def test_login_with_wrong_password_is_rejected(self):
        response = self.client.post("/api/auth/login/", {"username": "alice", "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("token", response.json())

    # --- Known business-logic findings (owner: Student 1). Remove the decorator once fixed. ---
    @unittest.expectedFailure
    def test_customer_cannot_change_order_status(self):
        self.auth(self.alice)
        self.client.put(f"/api/orders/{self.alice_order.id}/", {"status": "delivered"}, format="json")
        self.alice_order.refresh_from_db()
        self.assertEqual(self.alice_order.status, "pending")

    @unittest.expectedFailure
    def test_zero_quantity_order_is_rejected(self):
        self.auth(self.alice)
        response = self.client.post("/api/orders/", {"phone": self.phone.id, "quantity": 0}, format="json")
        self.assertEqual(response.status_code, 400)
