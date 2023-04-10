from pydantic import BaseSettings


class Settings(BaseSettings):
    huggingface_key: str = ""
    processor: str = "katanaml-org/invoices-donut-model-v1"
    model: str = "katanaml-org/invoices-donut-model-v1"
    inference_stats_file: str = "data/donut_inference_stats.json"
    training_stats_file: str = "data/donut_training_stats.json"


settings = Settings()