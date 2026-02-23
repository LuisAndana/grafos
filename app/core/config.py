from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
