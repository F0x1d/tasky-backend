from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://tasks:tasks@localhost:5432/tasks"
    public_key_path: str = "/app/keys/public_key.pem"
    algorithm: str = "RS256"


settings = Settings()
