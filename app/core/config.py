from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_file_path: str = "data/plan_combined.json"

    class Config:
        env_file = ".env"


settings = Settings()
