from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_file_path: str = "data/plan_combined.json"
    async_database_dsn: str = "postgresql+asyncpg://utmn_user:utmn_password@localhost:5432/utmn_map"
    database_dsn: str = "postgresql://utmn_user:utmn_password@localhost:5432/utmn_map"
    app_environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
