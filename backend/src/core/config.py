"""
Configuration settings for Content Engine backend.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # GCP Configuration
    gcp_project_id: str | None = Field(default=None, description="GCP Project ID")
    firestore_database_id: str = Field(default="main-db", description="Firestore Database ID")
    default_region: str = Field(default="europe-west2", description="Default GCP region")

    # OpenAI Configuration
    openai_api_key: str | None = Field(default=None, description="OpenAI API Key")
    enable_llm_scoring: bool = Field(
        default=True, description="Enable LLM-based scoring (audience fit, integrity)"
    )
    max_llm_cost_per_run: float = Field(
        default=1.0, description="Maximum cost in USD per scoring run (fail fast if exceeded)"
    )

    # Style Enhancement Configuration
    enable_style_enhancement: bool = Field(
        default=False, description="Enable style enhancement in content generation"
    )
    max_daily_extraction_cost: float = Field(
        default=5.0, description="Maximum daily cost in USD for style extraction"
    )
    max_style_context_tokens: int = Field(
        default=500, description="Maximum tokens for style context in prompts"
    )

    # Environment
    environment: str = Field(default="local", description="Environment: local, staging, prod")

    # GCS Configuration
    gcs_bucket_name: str = Field(default="", description="GCS Bucket Name")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }

    def get_openai_key(self) -> str:
        """Get OpenAI API key, raising error if not configured."""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required but not configured")
        return self.openai_api_key


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
