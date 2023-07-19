from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    sparrow_key: str = os.environ.get("SPARROW_KEY")
    api_data_url: str = os.environ.get("API_DATA_URL")


settings = Settings()
