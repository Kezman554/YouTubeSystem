"""
Configuration management for the Content Intelligence System.

Loads environment variables from .env file and provides typed access.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class Config:
    """
    Application configuration loaded from environment variables.

    Required environment variables:
    - YOUTUBE_API_KEY: YouTube Data API v3 key
    - ANTHROPIC_API_KEY: Anthropic API key for Claude

    Raises:
        ConfigError: If required environment variables are missing
    """

    def __init__(self):
        """Initialize configuration by loading environment variables."""
        # Load .env file from project root
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)

        # Load and validate required API keys
        self.youtube_api_key = self._get_required("YOUTUBE_API_KEY")
        self.anthropic_api_key = self._get_required("ANTHROPIC_API_KEY")

        # Optional: Database path (defaults to data/content.db)
        self.db_path = self._get_optional(
            "DB_PATH",
            default=str(Path(__file__).parent.parent / "data" / "content.db")
        )

    def _get_required(self, key: str) -> str:
        """
        Get a required environment variable.

        Args:
            key: Environment variable name

        Returns:
            The environment variable value

        Raises:
            ConfigError: If the environment variable is missing or empty
        """
        value = os.getenv(key)
        if not value:
            raise ConfigError(
                f"Missing required environment variable: {key}\n"
                f"Please set {key} in your .env file.\n"
                f"See .env.example for reference."
            )
        return value

    def _get_optional(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an optional environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            The environment variable value or default
        """
        return os.getenv(key, default)


# Global config instance
# Import this in other modules: from src.config import config
try:
    config = Config()
except ConfigError as e:
    # Re-raise with helpful context
    raise ConfigError(
        f"Configuration error: {e}\n\n"
        "To fix this:\n"
        "1. Copy .env.example to .env\n"
        "2. Fill in your API keys\n"
        "3. Run the application again"
    ) from e
