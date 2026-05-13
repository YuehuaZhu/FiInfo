from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="")

    twitter_auth_token: str = ""
    twitter_api_bearer: str = ""
    twitter_write_consumer_key: str = ""
    twitter_write_consumer_secret: str = ""
    twitter_write_access_token: str = ""
    twitter_write_access_secret: str = ""

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    data_dir: Path = Field(default=Path("./data"))
    tz: str = "Asia/Shanghai"
    daily_limit_per_category: int = 30
    top_kol_ratio: float = 0.25

    @property
    def has_twitter_read(self) -> bool:
        return bool(self.twitter_auth_token or self.twitter_api_bearer)

    @property
    def has_twitter_write(self) -> bool:
        return all([
            self.twitter_write_consumer_key,
            self.twitter_write_consumer_secret,
            self.twitter_write_access_token,
            self.twitter_write_access_secret,
        ])

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key)


def get_settings() -> Settings:
    """Re-read .env each call so tests with monkeypatch see fresh values."""
    s = Settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    return s


settings = get_settings()
