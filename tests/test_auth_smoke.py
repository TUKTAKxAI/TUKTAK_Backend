import os
import unittest

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "tuktak_test")
os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef")

from fastapi.testclient import TestClient
from sqlalchemy.orm import configure_mappers

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.settings import settings
from app.middleware.auth_cookies import AuthCookieMiddleware
from app.schemas.auth import CustomerSignupRequest
from app.schemas.auth import SignupResponse
from app.services.auth import _merge_user_type
from main import app


class AuthSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configure_mappers()

    def test_password_hash_and_access_token(self) -> None:
        password_hash = hash_password("Passw0rd!")
        self.assertTrue(verify_password("Passw0rd!", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

        token, _, _ = create_access_token(7, "BOTH")
        claims = decode_token(token, "access")
        self.assertEqual(claims["sub"], "7")
        self.assertEqual(claims["user_type"], "BOTH")

    def test_role_extension_supports_both_accounts(self) -> None:
        self.assertEqual(_merge_user_type("CUSTOMER", "CONTRACTOR"), "BOTH")
        self.assertEqual(_merge_user_type("CONTRACTOR", "CUSTOMER"), "BOTH")
        self.assertEqual(_merge_user_type("BOTH", "CUSTOMER"), "BOTH")

        response = SignupResponse.model_validate(
            {
                "user_id": 1,
                "user_type": "BOTH",
                "created_at": "2026-07-07T00:00:00Z",
            }
        )
        self.assertEqual(response.user_type, "BOTH")

    def test_openapi_contains_auth_contract(self) -> None:
        expected = {
            "/api/v1/agreements/required",
            "/api/v1/auth/signup/customer",
            "/api/v1/auth/signup/contractor",
            "/api/v1/auth/email-availability",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
        }
        self.assertTrue(expected.issubset(app.openapi()["paths"]))

    def test_auth_cookie_middleware_registered(self) -> None:
        self.assertTrue(
            any(item.cls is AuthCookieMiddleware for item in app.user_middleware)
        )

    def test_logout_without_body_clears_auth_cookies(self) -> None:
        with TestClient(app) as client:
            response = client.post("/api/v1/auth/logout")
            self.assertEqual(response.status_code, 200)
            set_cookie = response.headers.get("set-cookie", "")
            self.assertIn(settings.auth_access_cookie_name, set_cookie)
            self.assertIn(settings.auth_refresh_cookie_name, set_cookie)

    def test_public_health_and_agreement_routes(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").json(), {"status": "ok"})
            response = client.get("/api/v1/agreements/required")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()["agreements"]), 4)

    def test_password_policy_rejects_weak_password(self) -> None:
        with self.assertRaises(ValueError):
            CustomerSignupRequest.model_validate(
                {
                    "email": "user@example.com",
                    "password": "onlyletters",
                    "nickname": "user",
                    "name": "User",
                    "agreements": [
                        {
                            "terms_type": "TERMS_OF_SERVICE",
                            "terms_version": "1.0",
                            "is_agreed": True,
                        }
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
