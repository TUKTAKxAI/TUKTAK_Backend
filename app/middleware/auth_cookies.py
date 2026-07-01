from collections.abc import Awaitable, Callable
from http.cookies import SimpleCookie

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.settings import settings


class AuthCookieMiddleware(BaseHTTPMiddleware):
    """Bridge HttpOnly auth cookies with the existing Bearer-token dependencies."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.access_cookie_name = settings.auth_access_cookie_name
        self.refresh_cookie_name = settings.auth_refresh_cookie_name
        self.cookie_domain = settings.auth_cookie_domain
        self.cookie_secure = settings.auth_cookie_secure_enabled
        self.cookie_samesite = settings.auth_cookie_samesite
        self.api_prefix = settings.api_v1_prefix.rstrip("/")
        self.auth_cookie_path = f"{self.api_prefix}/auth" if self.api_prefix else "/auth"

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        self._inject_authorization_header(request)
        response = await call_next(request)

        if getattr(request.state, "clear_auth_cookies", False):
            self._clear_auth_cookies(response)
            return response

        tokens = getattr(request.state, "auth_tokens", None)
        if tokens is not None:
            self._set_auth_cookies(
                response,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
            )
        return response

    def _inject_authorization_header(self, request: Request) -> None:
        if b"authorization" in {key.lower() for key, _ in request.scope["headers"]}:
            return
        access_token = self._get_cookie_from_scope(request, self.access_cookie_name)
        if not access_token:
            return
        request.scope["headers"].append(
            (b"authorization", f"Bearer {access_token}".encode("latin-1"))
        )

    @staticmethod
    def _get_cookie_from_scope(request: Request, name: str) -> str | None:
        cookie_header = None
        for key, value in request.scope["headers"]:
            if key.lower() == b"cookie":
                cookie_header = value.decode("latin-1")
                break
        if cookie_header is None:
            return None
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        morsel = cookies.get(name)
        return morsel.value if morsel is not None else None

    def _set_auth_cookies(
        self,
        response: Response,
        access_token: str,
        refresh_token: str | None,
    ) -> None:
        response.set_cookie(
            key=self.access_cookie_name,
            value=access_token,
            max_age=settings.access_token_expire_seconds,
            httponly=True,
            secure=self.cookie_secure,
            samesite=self.cookie_samesite,
            domain=self.cookie_domain,
            path="/",
        )
        if refresh_token is None:
            return
        response.set_cookie(
            key=self.refresh_cookie_name,
            value=refresh_token,
            max_age=settings.refresh_token_expire_seconds,
            httponly=True,
            secure=self.cookie_secure,
            samesite=self.cookie_samesite,
            domain=self.cookie_domain,
            path=self.auth_cookie_path,
        )

    def _clear_auth_cookies(self, response: Response) -> None:
        response.delete_cookie(
            key=self.access_cookie_name,
            domain=self.cookie_domain,
            path="/",
            secure=self.cookie_secure,
            samesite=self.cookie_samesite,
            httponly=True,
        )
        response.delete_cookie(
            key=self.refresh_cookie_name,
            domain=self.cookie_domain,
            path=self.auth_cookie_path,
            secure=self.cookie_secure,
            samesite=self.cookie_samesite,
            httponly=True,
        )
