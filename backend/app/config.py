from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://lenny:lenny@127.0.0.1:5433/lenny"
    demo_user_id: str = "00000000-0000-0000-0000-000000000001"
    demo_user_name: str = "Growth Team"
    data_dir: str = str(
        REPO_ROOT / "data" / "lenny"
        if (REPO_ROOT / "data" / "lenny" / "index.json").exists()
        else REPO_ROOT / "data" / "sample"
    )
    llm_provider: str = "ollama"
    chat_model: str = "llama3.2"
    ollama_base_url: str = "http://127.0.0.1:11434"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 120

    def active_model(self) -> str:
        if self.llm_provider == "openai":
            return self.openai_model
        return self.chat_model


settings = Settings()
