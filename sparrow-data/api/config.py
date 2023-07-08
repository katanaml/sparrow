from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    huggingface_key: str = os.environ.get("HUGGINGFACE_KEY")
    sparrow_key: str = os.environ.get("SPARROW_KEY")
    secure_key: str = os.environ.get("SECURE_KEY")
    dataset_name: str = "katanaml-org/invoices-donut-data-v1"
    ocr_stats_file: str = "data/ocr_stats.json"


settings = Settings()
