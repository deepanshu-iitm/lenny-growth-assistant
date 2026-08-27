from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://lenny:lenny@127.0.0.1:5433/lenny"
    demo_user_id: str = "00000000-0000-0000-0000-000000000001"
    demo_user_name: str = "Growth Team"


settings = Settings()
