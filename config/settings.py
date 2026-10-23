"""
ONE: Always-On Autonomous AI Agent System
Configuration and Environment Settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Ensure workspace .env overrides any conflicting system-wide environment variables
_BASE_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BASE_DIR / ".env"
if _ENV_FILE.exists():
    load_dotenv(dotenv_path=str(_ENV_FILE), override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # System Info
    PROJECT_NAME: str = "ONE DOTS"
    VERSION: str = "3.5.0"
    TAGLINE: str = "Always-On Autonomous AI Agents Powered by Google Gemini & Dedicated Cloud Computers"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "one_state.db"
    SANDBOX_BASE_DIR: Path = DATA_DIR / "sandboxes"
    BROWSER_SESSIONS_DIR: Path = DATA_DIR / "browser_sessions"
    SCREENSHOTS_DIR: Path = DATA_DIR / "screenshots"
    REPORTS_DIR: Path = DATA_DIR / "reports"

    # API Keys & LLM Routing
    OPENAI_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")
    DEFAULT_MODEL: str = "gemini-3.5-flash-lite"
    LLM_PROVIDER: str = "gemini"

    # Agent Engine Controls
    HEARTBEAT_INTERVAL_SECONDS: int = 60
    MAX_CYCLES_PER_TICK: int = 10
    AUTO_APPROVE_SAFE_ACTIONS: bool = True
    HUMAN_APPROVAL_TIMEOUT_SECONDS: int = 3600  # 1 hour before reminder

    # External Notification Channels
    SLACK_WEBHOOK_URL: str = Field(default="")
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")
    WEBHOOK_ALERT_URL: str = Field(default="")

    # API Server
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000


settings = Settings()

# Ensure required runtime directories exist
for path in [
    settings.DATA_DIR,
    settings.SANDBOX_BASE_DIR,
    settings.BROWSER_SESSIONS_DIR,
    settings.SCREENSHOTS_DIR,
    settings.REPORTS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)
