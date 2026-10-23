"""
ONE: Always-On Autonomous AI Agent System
Configuration and Environment Settings
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # System Info
    PROJECT_NAME: str = "ONE"
    VERSION: str = "1.0.0"
    TAGLINE: str = "Persistent, Always-On Autonomous AI Agent System"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "one_state.db"
    SANDBOX_BASE_DIR: Path = DATA_DIR / "sandboxes"
    BROWSER_SESSIONS_DIR: Path = DATA_DIR / "browser_sessions"
    SCREENSHOTS_DIR: Path = DATA_DIR / "screenshots"
    REPORTS_DIR: Path = DATA_DIR / "reports"

    # API Keys & LLM Routing
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    DEFAULT_MODEL: str = "gpt-4o"
    LLM_PROVIDER: str = "mock"  # default to 'mock' if no key provided, otherwise 'openai' / 'gemini'

    # Agent Engine Controls
    HEARTBEAT_INTERVAL_SECONDS: int = 60
    MAX_CYCLES_PER_TICK: int = 10
    AUTO_APPROVE_SAFE_ACTIONS: bool = True
    HUMAN_APPROVAL_TIMEOUT_SECONDS: int = 3600  # 1 hour before reminder

    # External Notification Channels
    SLACK_WEBHOOK_URL: str = Field(default="", env="SLACK_WEBHOOK_URL")
    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(default="", env="TELEGRAM_CHAT_ID")
    WEBHOOK_ALERT_URL: str = Field(default="", env="WEBHOOK_ALERT_URL")

    # API Server
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


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
