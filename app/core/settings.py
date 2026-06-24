from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
