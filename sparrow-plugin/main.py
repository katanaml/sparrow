import quart
import quart_cors
from quart import request, send_from_directory
import requests
from config import settings


app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")


# Provides info how to upload receipt
@app.get("/upload_receipt_info/<string:username>")
async def get_upload_receipt_info(username):
    print("Get upload receipt info for user: " + username)
    return quart.Response(response='This is the URL: http://localhost:7860', status=200)


# Fetching OCR'ed raw receipt data into ChatGPT
@app.get("/receipt_data/<string:username>")
async def get_receipt_data(username):
    receipt_id = request.args.get("receipt_id")
    print("Get receipt data for user: " + username, "receipt_id: " + receipt_id)

    url = settings.api_url_get_receipt_data

    params = {
        'receipt_id': receipt_id,
        'sparrow_key': settings.sparrow_key
    }

    response = requests.get(url, params=params, timeout=180)

    if response.status_code != 200:
        error_text = "Error: " + str(response.status_code) + " " + response.text
        return quart.Response(response=error_text, status=400)

    return quart.Response(response=response.json(), status=200)


# Storing structured processed receipt data into DB
@app.post("/receipt_storage_db/<string:username>")
async def add_receipt_data_to_db(username):
    receipt_id = request.args.get("receipt_id")
    receipt_json = request.args.get("receipt_json")
    print("Add receipt data for user: " + username, "receipt_id: " + receipt_id)

    url = settings.api_url_add_receipt_data_to_db

    data = {
        'chatgpt_user': username,
        'receipt_id': receipt_id,
        'receipt_content': receipt_json,
        'sparrow_key': settings.sparrow_key
    }

    response = requests.post(url, data=data, timeout=180)

    return quart.Response(response)


# Fetching structured processed receipt data from DB by ID
@app.get("/receipt_storage_db/<string:username>")
async def get_receipt_data_from_db(username):
    receipt_id = request.args.get("receipt_id")
    print("Get receipt data from DB for user: " + username, "receipt_id: " + receipt_id)

    url = settings.api_url_get_receipt_data_from_db

    params = {
        'chatgpt_user': username,
        'receipt_id': receipt_id,
        'sparrow_key': settings.sparrow_key
    }

    response = requests.get(url, params=params, timeout=180)

    if response.status_code != 200:
        error_text = "Error: " + str(response.status_code) + " " + response.text
        return quart.Response(response=error_text, status=400)

    return quart.Response(response=response, status=200)


# Deleting structured processed receipt data from DB by ID
@app.delete("/receipt_storage_db/<string:username>")
async def remove_receipt_data_from_db(username):
    receipt_id = request.args.get("receipt_id")
    print("Delete receipt data from DB for user: " + username, "receipt_id: " + receipt_id)

    url = settings.api_url_remove_receipt_data_from_db

    params = {
        'chatgpt_user': username,
        'receipt_id': receipt_id,
        'sparrow_key': settings.sparrow_key
    }

    response = requests.delete(url, params=params, timeout=180)

    if response.status_code != 200:
        error_text = "Error: " + str(response.status_code) + " " + response.text
        return quart.Response(response=error_text, status=400)

    return quart.Response(response)


# Fetching list of processed receipt data IDs from DB
@app.get("/receipts_storage_ids_db/<string:username>")
async def get_receipts_data_ids_from_db(username):
    print("Get receipt data IDs from DB for user: " + username)

    url = settings.api_url_get_receipts_data_ids_from_db

    params = {
        'chatgpt_user': username,
        'sparrow_key': settings.sparrow_key
    }

    response = requests.get(url, params=params, timeout=180)

    if response.status_code != 200:
        error_text = "Error: " + str(response.status_code) + " " + response.text
        return quart.Response(response=error_text, status=400)

    return quart.Response(response=response, status=200)


# Fetching content of all stored receipts in DB
@app.get("/receipts_storage_content_db/<string:username>")
async def get_receipts_data_content_from_db(username):
    print("Get receipt data content from DB for user: " + username)

    url = settings.api_url_get_receipts_data_content_from_db

    params = {
        'chatgpt_user': username,
        'sparrow_key': settings.sparrow_key
    }

    response = requests.get(url, params=params, timeout=180)

    if response.status_code != 200:
        error_text = "Error: " + str(response.status_code) + " " + response.text
        return quart.Response(response=error_text, status=400)

    return quart.Response(response=response, status=200)


@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")


@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")


@app.route('/legal.html')
async def legal():
    return await send_from_directory('static', 'legal.html')


def main():
    app.run(debug=True, host="0.0.0.0", port=5003)


if __name__ == "__main__":
    main()
