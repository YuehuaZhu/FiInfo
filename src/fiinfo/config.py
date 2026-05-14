from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="")

    # Twitter
    twitter_auth_token: str = Field(default="", validation_alias="TWITTER_AUTH_TOKEN")
    twitter_ct0: str = Field(default="", validation_alias="TWITTER_CT0")
    twitter_api_bearer: str = Field(default="", validation_alias="TWITTER_API_BEARER")
    twitter_write_consumer_key: str = Field(default="", validation_alias="TWITTER_WRITE_CONSUMER_KEY")
    twitter_write_consumer_secret: str = Field(default="", validation_alias="TWITTER_WRITE_CONSUMER_SECRET")
    twitter_write_access_token: str = Field(default="", validation_alias="TWITTER_WRITE_ACCESS_TOKEN")
    twitter_write_access_secret: str = Field(default="", validation_alias="TWITTER_WRITE_ACCESS_SECRET")

    # LLM — Anthropic Claude(官方或代理网关)
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    anthropic_auth_token: str = Field(default="", validation_alias="ANTHROPIC_AUTH_TOKEN")
    anthropic_base_url: str = Field(default="", validation_alias="ANTHROPIC_BASE_URL")
    anthropic_model: str = Field(default="claude-sonnet-4-6", validation_alias="ANTHROPIC_MODEL")

    # LLM — 豆包(火山方舟,OpenAI 兼容,200 万 token/天免费)
    ark_api_key: str = Field(default="", validation_alias="ARK_API_KEY")
    ark_base_url: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3",
        validation_alias="ARK_BASE_URL",
    )
    ark_model: str = Field(default="doubao-pro-32k", validation_alias="ARK_MODEL")

    # Runtime
    data_dir: Path = Field(default=Path("./data"), validation_alias="FIINFO_DATA_DIR")
    tz: str = Field(default="Asia/Shanghai", validation_alias="FIINFO_TZ")
    daily_limit_per_category: int = Field(default=30, validation_alias="FIINFO_DAILY_LIMIT_PER_CATEGORY")
    top_kol_ratio: float = Field(default=0.25, validation_alias="FIINFO_TOP_KOL_RATIO")

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
    def has_doubao(self) -> bool:
        return bool(self.ark_api_key)

    @property
    def has_claude(self) -> bool:
        return bool(self.anthropic_api_key or self.anthropic_auth_token)

    @property
    def has_llm(self) -> bool:
        return self.has_doubao or self.has_claude


def get_settings() -> Settings:
    s = Settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    return s


settings = get_settings()
