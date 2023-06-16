import json

import quart
import quart_cors
from quart import request

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

_RECEIPTS = {}

_RECEIPT_INFO = [
    'YOUR GUEST NUMBER IS',
    '43',
    'IN-N-OUT BURGER LINQ',
    '320 6 2166 6301',
    'Cashier: SERJI0 SA',
    'Check : 43',
    'TRANS #: 6301',
    '1 Db1-Dbl',
    '5.25',
    '+ Onion',
    '1 Fry',
    '2.35',
    '1 Med Soft Drink',
    '2.15',
    'COUNTER-Eat In',
    '9.75',
    'TAX 8.375%',
    '.82',
    'Amount Due',
    '$10.57',
    'Tender MasterCard',
    '$10.57',
    'Change',
    '$.00',
    'CHARGE DETAIL',
    'SALE',
    'Card Type:',
    'Mastercard',
    'Account :',
    '************5562 R',
    'Auth Code:',
    'NDTQU8',
    'Trans #:',
    '6301',
    'Auth Ref :',
    '2015517078',
    'AUTH AMT :',
    '$10.57',
    'AID:',
    'A0000000041010',
    'TVR :',
    '0000008001',
    'TSI:',
    '0000',
    'App Name:',
    'Debit MasterCard',
    'ARQC:',
    'ADCF5208793B7BD6',
    'THANK YOU!',
    'Quest ions/Comments: Cal1 800-786-1 :10',
    'L1 T6',
    '9:21 PM',
    '2021-11-30'
]


@app.get("/upload_receipt_info/<string:username>")
async def get_upload_receipt_info(username):
    print("Get upload receipt info for user: " + username)
    return quart.Response(response='This is the URL: http://127.0.0.1:7860', status=200)


@app.get("/receipt_data/<string:username>")
async def get_receipt_data(username):
    receipt_id = request.args.get("receipt_id")
    print("Get receipt data for user: " + username, "receipt_id: " + receipt_id)
    return quart.Response(response=json.dumps(_RECEIPT_INFO), status=200)


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


def main():
    app.run(debug=True, host="0.0.0.0", port=5003)


if __name__ == "__main__":
    main()
