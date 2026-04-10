from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/jinshouzhi"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret_key: str = "change-me"
    jwt_access_token_expire_minutes: int = 120
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    ernie_api_key: str = "replace-me"
    ernie_base_url: str = "https://qianfan.baidubce.com/v2"
    ernie_model: str = "ernie-5.0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
