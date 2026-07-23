from functools import lru_cache

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = Field("TukTak Backend", alias="APP_NAME")
    app_env: str = Field("local", alias="APP_ENV")
    debug: bool = Field(False, alias="APP_DEBUG")
    api_v1_prefix: str = Field("/api/v1", alias="API_V1_PREFIX")
    cors_origins_raw: str = Field(
        "http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_host: str = Field("localhost", alias="DB_HOST")
    db_port: int = Field(3306, alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")
    db_echo: bool = Field(False, alias="DB_ECHO")

    secret_key: str = Field(..., alias="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_seconds: int = Field(900, gt=0, alias="ACCESS_TOKEN_EXPIRE")
    refresh_token_expire_seconds: int = Field(
        604800, gt=0, alias="REFRESH_TOKEN_EXPIRE"
    )
    refresh_token_pepper: str | None = Field(None, alias="REFRESH_TOKEN_PEPPER")
    auth_access_cookie_name: str = Field("tuktak_access_token", alias="AUTH_ACCESS_COOKIE_NAME")
    auth_refresh_cookie_name: str = Field("tuktak_refresh_token", alias="AUTH_REFRESH_COOKIE_NAME")
    auth_cookie_domain: str | None = Field(None, alias="AUTH_COOKIE_DOMAIN")
    auth_cookie_secure: bool | None = Field(None, alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        "lax",
        alias="AUTH_COOKIE_SAMESITE",
    )
    ai_stub_delay_seconds: float = Field(3.0, ge=0, alias="AI_STUB_DELAY_SECONDS")
    ai_service_url: str = Field("http://localhost:8001", alias="AI_SERVICE_URL")
    ai_service_timeout_seconds: float = Field(60.0, gt=0, alias="AI_SERVICE_TIMEOUT_SECONDS")
    aws_region: str = Field("ap-northeast-2", alias="AWS_REGION")
    s3_bucket_name: str | None = Field(None, alias="S3_BUCKET_NAME")
    ai_estimate_image_prefix: str = Field("ai-estimates", alias="AI_ESTIMATE_IMAGE_PREFIX")

    terms_of_service_version: str = Field("1.0", alias="TERMS_OF_SERVICE_VERSION")
    privacy_policy_version: str = Field("1.0", alias="PRIVACY_POLICY_VERSION")
    image_analysis_version: str = Field("1.0", alias="IMAGE_ANALYSIS_VERSION")
    matching_info_version: str = Field("1.0", alias="MATCHING_INFO_VERSION")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]

    @property
    def async_database_url(self) -> URL:
        return URL.create(
            drivername="mysql+asyncmy",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )

    @property
    def sync_database_url(self) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )

    @property
    def token_pepper(self) -> str:
        return self.refresh_token_pepper or self.secret_key

    @property
    def auth_cookie_secure_enabled(self) -> bool:
        if self.auth_cookie_secure is not None:
            return self.auth_cookie_secure
        return self.app_env.lower() not in {"local", "dev", "development", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
