import requests


def evaluate_call(api_url, model_in_use, sparrow_key):
    data = {
        'model_in_use': model_in_use,
        'sparrow_key': sparrow_key
    }

    response = requests.post(api_url, data=data)
    if response.status_code != 200:
        print('Request failed with status code:', response.status_code)
        print('Response:', response.text)

    return response.text
