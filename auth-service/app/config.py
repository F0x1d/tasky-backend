from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://auth:auth@localhost:5432/auth"
    private_key_path: str = "/app/keys/private_key.pem"
    public_key_path: str = "/app/keys/public_key.pem"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "RS256"


settings = Settings()
