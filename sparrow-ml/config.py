from pydantic import BaseSettings


class Settings(BaseSettings):
    huggingface_key: str = ""
    donut_processor: str = "katanaml-org/invoices-donut-model-v1"
    donut_model: str = "katanaml-org/invoices-donut-model-v1"


settings = Settings()