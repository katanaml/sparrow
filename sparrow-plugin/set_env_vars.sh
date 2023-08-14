#!/bin/bash

# Set environment variables
export SPARROW_KEY=""
export API_URL_GET_RECEIPT_DATA="http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_by_id"
export API_URL_ADD_RECEIPT_DATA_TO_DB="http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/store_receipt_db"
export API_URL_GET_RECEIPT_DATA_FROM_DB="http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_db_by_id"
export API_URL_REMOVE_RECEIPT_DATA_FROM_DB="http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_db_by_id"
export API_URL_GET_RECEIPTS_DATA_IDS_FROM_DB="http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_db_ids_by_user"
export API_URL_GET_RECEIPTS_DATA_CONTENT_FROM_DB="http://127.0.0.1:8000/api-chatgpt-plugin/v1/sparrow-data/receipt_db_content_by_user"
export OAUTH_USERINFO_URL="https://abc.logto.app/oidc/me"
export SPARROW_UI_URL="http://localhost:7860"


# Print environment variables to verify they're set
echo "SPARROW_KEY: $SPARROW_KEY"
echo "API_URL_GET_RECEIPT_DATA: $API_URL_GET_RECEIPT_DATA"
echo "API_URL_ADD_RECEIPT_DATA_TO_DB: $API_URL_ADD_RECEIPT_DATA_TO_DB"
echo "API_URL_GET_RECEIPT_DATA_FROM_DB: $API_URL_GET_RECEIPT_DATA_FROM_DB"
echo "API_URL_REMOVE_RECEIPT_DATA_FROM_DB: $API_URL_REMOVE_RECEIPT_DATA_FROM_DB"
echo "API_URL_GET_RECEIPTS_DATA_IDS_FROM_DB: $API_URL_GET_RECEIPTS_DATA_IDS_FROM_DB"
echo "API_URL_GET_RECEIPTS_DATA_CONTENT_FROM_DB: $API_URL_GET_RECEIPTS_DATA_CONTENT_FROM_DB"
echo "OAUTH_USERINFO_URL: $OAUTH_USERINFO_URL"
echo "SPARROW_UI_URL: $SPARROW_UI_URL"