import requests


def training_call(api_url):
    response = requests.get(api_url)
    if response.status_code != 200:
        print('Request failed with status code:', response.status_code)
        print('Response:', response.text)

    return response.text
