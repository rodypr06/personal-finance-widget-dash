"""
Application configuration using pydantic-settings.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Database
    DATABASE_URL: str

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Security
    JWT_SECRET: str
    ALLOWED_ORIGINS: str = "http://localhost:8080"

    # Categorization thresholds
    LOW_CONFIDENCE: float = 0.80
    REVIEW_AMOUNT_CENTS: int = 5000  # Transactions above this amount go to review

    # Optional
    TELEGRAM_WEBHOOK_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
