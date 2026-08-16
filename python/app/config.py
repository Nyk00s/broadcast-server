from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Config(BaseSettings):
    app_port: int
    max_history: int

    cache_port: int
    cache_host: str

    jwt_secret: SecretStr
    jwt_algorithm: str
    access_token_ttl_minutes: int
    refresh_token_ttl_days: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )