"""
Community Assist Configuration
Centralized configuration management with validation
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    database_url: str = Field(
        default="postgresql://community_user:community_password@localhost:5432/community_assist",
        alias="DATABASE_URL"
    )
    postgres_user: str = Field(default="community_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="community_password", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="community_assist", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    # Application
    flask_env: str = Field(default="development", alias="FLASK_ENV")
    flask_debug: bool = Field(default=True, alias="FLASK_DEBUG")
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")
    default_language: str = Field(default="en", alias="DEFAULT_LANGUAGE")

    # Scraping
    scrape_delay_seconds: float = Field(default=2.5, alias="SCRAPE_DELAY_SECONDS")
    max_concurrent_requests: int = Field(default=3, alias="MAX_CONCURRENT_REQUESTS")
    max_crawl_depth: int = Field(default=3, alias="MAX_CRAWL_DEPTH")
    user_agent: str = Field(
        default="CommunityAssist/1.0 (https://github.com/thingvallatech/community-assist)",
        alias="USER_AGENT"
    )

    # Scraping tiers
    enable_tier1: bool = Field(default=True, alias="ENABLE_TIER1")
    enable_tier2: bool = Field(default=True, alias="ENABLE_TIER2")
    enable_tier3: bool = Field(default=True, alias="ENABLE_TIER3")

    # Target Geography
    target_state: str = Field(default="FL", alias="TARGET_STATE")
    target_county: str = Field(default="Brevard", alias="TARGET_COUNTY")

    # External APIs
    google_maps_api_key: Optional[str] = Field(default=None, alias="GOOGLE_MAPS_API_KEY")
    benefits_gov_api_key: Optional[str] = Field(default=None, alias="BENEFITS_GOV_API_KEY")

    # Feature Flags
    enable_calculator: bool = Field(default=True, alias="ENABLE_CALCULATOR")
    enable_locator: bool = Field(default=True, alias="ENABLE_LOCATOR")
    enable_pdf_generation: bool = Field(default=False, alias="ENABLE_PDF_GENERATION")
    enable_chatbot: bool = Field(default=False, alias="ENABLE_CHATBOT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Data Import
    sql_dump_url: Optional[str] = Field(default=None, alias="SQL_DUMP_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.flask_env == "production"

    @property
    def database_connection_string(self) -> str:
        """Get database URL, preferring DATABASE_URL if set."""
        if self.database_url and "://" in self.database_url:
            return self.database_url
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    def get_fpl_percentage_limit(self, percentage: int, household_size: int, year: int = 2024) -> float:
        """
        Calculate income limit based on FPL percentage.
        Common percentages: 100%, 130% (SNAP), 138% (Medicaid), 200%, 250%, 400%
        """
        # 2024 FPL base amounts (48 contiguous states)
        fpl_2024 = {
            1: 15060, 2: 20440, 3: 25820, 4: 31200,
            5: 36580, 6: 41960, 7: 47340, 8: 52720
        }

        # For households larger than 8, add $5,380 per person
        if household_size > 8:
            base = fpl_2024[8] + (household_size - 8) * 5380
        else:
            base = fpl_2024.get(household_size, fpl_2024[1])

        return (base * percentage) / 100


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
