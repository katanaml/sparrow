from pydantic import BaseSettings


class Settings(BaseSettings):
    huggingface_key: str = ""
    donut_processor: str = "katanaml-org/invoices-donut-model-v1"
    donut_model: str = "katanaml-org/invoices-donut-model-v1"
    donut_inference_stats_file: str = "data/donut_inference_stats.json"


settings = Settings()