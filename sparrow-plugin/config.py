from pydantic import BaseSettings


class Settings(BaseSettings):
    sparrow_key: str = ""
    api_url_get_receipt_data = "http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_by_id"
    api_url_add_receipt_data_processed = "http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/store_receipt_processed"


settings = Settings()