from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):
    """Staff login (token + rol) va joriy foydalanuvchi (me)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="kassir1", password="secret123", role=User.Role.KASSIR
        )

    def test_login_returns_token_and_role(self):
        res = self.client.post(
            "/api/auth/login/",
            {"username": "kassir1", "password": "secret123"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("token", res.data)
        self.assertEqual(res.data["role"], "kassir")

    def test_login_wrong_password_rejected(self):
        res = self.client.post(
            "/api/auth/login/",
            {"username": "kassir1", "password": "wrong"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_me_requires_auth(self):
        res = self.client.get("/api/auth/me/")
        self.assertIn(res.status_code, (401, 403))

    def test_me_returns_current_user(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["username"], "kassir1")
        self.assertEqual(res.data["role"], "kassir")


class UserModelTests(APITestCase):
    def test_role_properties(self):
        kassir = User.objects.create_user(username="k", password="x", role=User.Role.KASSIR)
        oshpaz = User.objects.create_user(username="o", password="x", role=User.Role.OSHPAZ)
        self.assertTrue(kassir.is_kassir)
        self.assertFalse(kassir.is_oshpaz)
        self.assertTrue(oshpaz.is_oshpaz)
        self.assertFalse(oshpaz.is_kassir)
