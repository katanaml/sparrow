from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    sparrow_key: str = os.environ.get("SPARROW_KEY")
    api_url_get_receipt_data = os.environ.get("API_URL_GET_RECEIPT_DATA")
    api_url_add_receipt_data_to_db = os.environ.get("API_URL_ADD_RECEIPT_DATA_TO_DB")
    api_url_get_receipt_data_from_db = os.environ.get("API_URL_GET_RECEIPT_DATA_FROM_DB")
    api_url_remove_receipt_data_from_db = os.environ.get("API_URL_REMOVE_RECEIPT_DATA_FROM_DB")
    api_url_get_receipts_data_ids_from_db = os.environ.get("API_URL_GET_RECEIPTS_DATA_IDS_FROM_DB")
    api_url_get_receipts_data_content_from_db = os.environ.get("API_URL_GET_RECEIPTS_DATA_CONTENT_FROM_DB")
    oauth_userinfo_url = os.environ.get("OAUTH_USERINFO_URL")
    sparrow_ui_url = os.environ.get("SPARROW_UI_URL")


settings = Settings()
