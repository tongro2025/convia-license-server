"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict

# Plan to max containers mapping
# -1 means unlimited
PLAN_MAX_CONTAINERS = {
    "basic": 1,
    "pro": 5,
    "enterprise": -1,  # unlimited
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    app_env: str = "dev"  # dev, prod, staging

    # Database
    database_url: str

    # Paddle
    paddle_webhook_secret: str

    # Admin API
    admin_api_key: str

    # JWT
    license_jwt_secret: str

    # Email (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@convia.vip"
    smtp_from_name: str = "Convia License Server"
    smtp_use_tls: bool = True

    # Frontend URL for magic links
    frontend_url: str = "https://convia.vip"

    # pydantic-settings v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # APP_ENV / app_env 둘 다 허용
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "prod"


settings = Settings()