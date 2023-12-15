import requests


def training_call(api_url, max_epochs, val_check_interval, warmup_steps, model_in_use, sparrow_key):
    data = {
        'max_epochs': max_epochs,
        'val_check_interval': val_check_interval,
        'warmup_steps': warmup_steps,
        'model_in_use': model_in_use,
        'sparrow_key': sparrow_key
    }

    response = requests.post(api_url, data=data)
    if response.status_code != 200:
        print('Request failed with status code:', response.status_code)
        print('Response:', response.text)

    return response.text
