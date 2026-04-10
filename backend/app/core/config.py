from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Golden Finger API'
    api_v1_str: str = '/api'
    secret_key: str = 'change-me'
    access_token_expire_minutes: int = 1440
    database_url: str = 'sqlite:///./golden_finger.db'
    redis_url: str = 'redis://localhost:6379/0'
    ernie_api_key: str = 'replace-me'


@lru_cache
def get_settings() -> Settings:
    return Settings()
