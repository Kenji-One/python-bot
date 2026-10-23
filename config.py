"""
Configuration management for PowerPlay Lead Claimer Bot
Handles environment variables and application settings
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class"""

    # Base directories
    BASE_DIR = Path(__file__).parent
    LOGS_DIR = BASE_DIR / "logs"
    SCREENSHOTS_DIR = BASE_DIR / "screenshots"

    # PowerPlay credentials
    USERNAME: str = os.getenv("POWERPLAY_USERNAME", "")
    PASSWORD: str = os.getenv("POWERPLAY_PASSWORD", "")

    # PowerPlay URLs
    BASE_URL: str = "https://powerplay.generac.com"
    LOGIN_URL: str = f"{BASE_URL}/app/"
    DASHBOARD_URL: str = f"{BASE_URL}/app/"

    # Bot behavior settings
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"
    POLLING_INTERVAL_MS: int = int(os.getenv("POLLING_INTERVAL_MS", "400"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY_SECONDS: int = int(os.getenv("RETRY_DELAY_SECONDS", "5"))

    # Timeouts (in milliseconds)
    PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "30000"))
    ELEMENT_TIMEOUT: int = int(os.getenv("ELEMENT_TIMEOUT", "5000"))
    CLAIM_BUTTON_TIMEOUT: int = int(os.getenv("CLAIM_BUTTON_TIMEOUT", "2000"))

    # Features
    ENABLE_SOUND_NOTIFICATION: bool = os.getenv("ENABLE_SOUND_NOTIFICATION", "true").lower() == "true"
    ENABLE_SCREENSHOTS: bool = os.getenv("ENABLE_SCREENSHOTS", "true").lower() == "true"
    ENABLE_AUTO_RESTART: bool = os.getenv("ENABLE_AUTO_RESTART", "true").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"

    # Email notifications (via Brevo)
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")


    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.USERNAME or not cls.PASSWORD:
            raise ValueError(
                "Missing required credentials. "
                "Please set POWERPLAY_USERNAME and POWERPLAY_PASSWORD in .env file"
            )
        return True

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure required directories exist"""
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.SCREENSHOTS_DIR.mkdir(exist_ok=True)
