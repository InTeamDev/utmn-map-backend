from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_file_path: str = "data/plan_combined.json"
    async_database_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    database_dsn: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    app_environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
