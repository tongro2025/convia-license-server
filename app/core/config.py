"""Application configuration management."""

from pydantic_settings import BaseSettings

# Plan to max containers mapping
# -1 means unlimited
PLAN_MAX_CONTAINERS = {
    "basic": 1,
    "pro": 5,
    "enterprise": -1,  # unlimited
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str
    paddle_webhook_secret: str
    admin_api_key: str
    license_jwt_secret: str

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()





