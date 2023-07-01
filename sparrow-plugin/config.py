from pydantic import BaseSettings


class Settings(BaseSettings):
    sparrow_key: str = ""
    api_url_get_receipt_data = "http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_by_id"
    api_url_add_receipt_data_to_db = "http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/store_receipt_db"
    api_url_get_receipt_data_from_db = "http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_db_by_id"
    api_url_remove_receipt_data_from_db = "http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_db_by_id"
    api_url_get_receipts_data_ids_from_db = "http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_db_ids_by_user"
    api_url_get_receipts_data_content_from_db = "http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_db_content_by_user"


settings = Settings()