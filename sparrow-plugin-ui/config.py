from pydantic import BaseSettings


class Settings(BaseSettings):
    sparrow_key: str = ""


settings = Settings()