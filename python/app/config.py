from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    app_port: int
    max_history: int

    cache_port: int
    cache_host: str
    cache_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )