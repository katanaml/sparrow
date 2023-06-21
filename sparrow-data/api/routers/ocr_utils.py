import secrets
import string


def merge_data(values):
    data = []
    for idx in range(len(values)):
        data.append([values[idx][1][0]])
        # print(data[idx])

    return data


def store_data(data):
    print("Storing data...")

    key = generate_key()

    return key


def generate_key(length=10):
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for i in range(length))
    return key