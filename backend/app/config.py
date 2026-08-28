from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://lenny:lenny@127.0.0.1:5433/lenny"
    demo_user_id: str = "00000000-0000-0000-0000-000000000001"
    demo_user_name: str = "Growth Team"
    data_dir: str = str(REPO_ROOT / "data" / "sample")
    llm_provider: str = "ollama"
    chat_model: str = "llama3.2"
    ollama_base_url: str = "http://127.0.0.1:11434"
    llm_timeout_seconds: int = 120


settings = Settings()
