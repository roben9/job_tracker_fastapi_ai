from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Job Tracker"

    # Database details
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    # if we are using an api from an llm
    # gemini_api_key: str

    secret_key: str

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @property
    def database_url(self) -> URL:
        database_url = URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )
        return database_url


settings = Settings()
