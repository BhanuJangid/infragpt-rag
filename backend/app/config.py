from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InfraGPT"
    openai_api_key: str = ""
    groq_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    database_url: str = ""
    data_dir: Path = Path(__file__).resolve().parents[1] / "data"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
