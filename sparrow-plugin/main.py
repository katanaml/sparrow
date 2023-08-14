import quart
import quart_cors
from quart import request, send_from_directory
import requests
from config import settings


app = quart_cors.cors(quart.Quart(__name__), allow_origin="*")


def verify_auth_header(req):
    access_token = req.headers.get("Authorization")
    userinfo_url = settings.oauth_userinfo_url

    headers = {
        'Authorization': access_token
    }

    response = requests.get(userinfo_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        sub = data.get('sub')
        return sub
    else:
        return -1


# Provides info how to upload receipt
@app.get("/upload_receipt_info")
async def get_upload_receipt_info():
    sub = verify_auth_header(request)

    if sub != -1:
        print("Get upload receipt info for user: " + sub)
        return quart.Response(response='This is the URL: ' + settings.sparrow_ui_url, status=200)
    else:
        return quart.Response(response='Unauthorized', status=401)


# Fetching OCR'ed raw receipt data into ChatGPT
@app.get("/receipt_data")
async def get_receipt_data():
    sub = verify_auth_header(request)

    if sub != -1:
        receipt_id = request.args.get("receipt_id")
        print("Get receipt data for user: " + sub, "receipt_id: " + receipt_id)

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
    else:
        return quart.Response(response='Unauthorized', status=401)


# Storing structured processed receipt data into DB
@app.post("/receipt_storage_db")
async def add_receipt_data_to_db():
    sub = verify_auth_header(request)

    if sub != -1:
        receipt_id = request.args.get("receipt_id")
        receipt_json = request.args.get("receipt_json")
        print("Add receipt data for user: " + sub, "receipt_id: " + receipt_id)

        url = settings.api_url_add_receipt_data_to_db

        data = {
            'chatgpt_user': sub,
            'receipt_id': receipt_id,
            'receipt_content': receipt_json,
            'sparrow_key': settings.sparrow_key
        }

        response = requests.post(url, data=data, timeout=180)

        return quart.Response(response)
    else:
        return quart.Response(response='Unauthorized', status=401)


# Fetching structured processed receipt data from DB by ID
@app.get("/receipt_storage_db")
async def get_receipt_data_from_db():
    sub = verify_auth_header(request)

    if sub != -1:
        receipt_id = request.args.get("receipt_id")
        print("Get receipt data from DB for user: " + sub, "receipt_id: " + receipt_id)

        url = settings.api_url_get_receipt_data_from_db

        params = {
            'chatgpt_user': sub,
            'receipt_id': receipt_id,
            'sparrow_key': settings.sparrow_key
        }

        response = requests.get(url, params=params, timeout=180)

        if response.status_code != 200:
            error_text = "Error: " + str(response.status_code) + " " + response.text
            return quart.Response(response=error_text, status=400)

        return quart.Response(response=response, status=200)
    else:
        return quart.Response(response='Unauthorized', status=401)


# Deleting structured processed receipt data from DB by ID
@app.delete("/receipt_storage_db")
async def remove_receipt_data_from_db():
    sub = verify_auth_header(request)

    if sub != -1:
        receipt_id = request.args.get("receipt_id")
        print("Delete receipt data from DB for user: " + sub, "receipt_id: " + receipt_id)

        url = settings.api_url_remove_receipt_data_from_db

        params = {
            'chatgpt_user': sub,
            'receipt_id': receipt_id,
            'sparrow_key': settings.sparrow_key
        }

        response = requests.delete(url, params=params, timeout=180)

        if response.status_code != 200:
            error_text = "Error: " + str(response.status_code) + " " + response.text
            return quart.Response(response=error_text, status=400)

        return quart.Response(response)
    else:
        return quart.Response(response='Unauthorized', status=401)


# Fetching list of processed receipt data IDs from DB
@app.get("/receipts_storage_ids_db")
async def get_receipts_data_ids_from_db():
    sub = verify_auth_header(request)

    if sub != -1:
        print("Get receipt data IDs from DB for user: " + sub)

        url = settings.api_url_get_receipts_data_ids_from_db

        params = {
            'chatgpt_user': sub,
            'sparrow_key': settings.sparrow_key
        }

        response = requests.get(url, params=params, timeout=180)

        if response.status_code != 200:
            error_text = "Error: " + str(response.status_code) + " " + response.text
            return quart.Response(response=error_text, status=400)

        return quart.Response(response=response, status=200)
    else:
        return quart.Response(response='Unauthorized', status=401)


# Fetching content of all stored receipts in DB
@app.get("/receipts_storage_content_db")
async def get_receipts_data_content_from_db():
    sub = verify_auth_header(request)

    if sub != -1:
        print("Get receipt data content from DB for user: " + sub)

        url = settings.api_url_get_receipts_data_content_from_db

        params = {
            'chatgpt_user': sub,
            'sparrow_key': settings.sparrow_key
        }

        response = requests.get(url, params=params, timeout=180)

        if response.status_code != 200:
            error_text = "Error: " + str(response.status_code) + " " + response.text
            return quart.Response(response=error_text, status=400)

        return quart.Response(response=response, status=200)
    else:
        return quart.Response(response='Unauthorized', status=401)


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
    app.run(debug=False, host="0.0.0.0", port=5003)


if __name__ == "__main__":
    main()
