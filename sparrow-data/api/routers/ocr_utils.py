import secrets
import string
from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError
from typing import List
import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
import base64


# Define a key. Note: it must be of length 16, 24, or 32.
secure_key = ""


def encrypt(plain_text: str, key: bytes) -> str:
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    encrypted_text = cipher.encrypt(pad(plain_text.encode(), AES.block_size))
    return b64encode(iv + encrypted_text).decode()


def decrypt(encrypted_text: str, key: bytes) -> str:
    decrypted_text = b64decode(encrypted_text)
    iv = decrypted_text[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    decrypted_text = unpad(cipher.decrypt(decrypted_text[16:]), AES.block_size)
    return decrypted_text.decode()


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ReceiptModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    receipt_key: str = Field(..., description="The unique key for the receipt.")
    content: List[List[str]] = Field(..., description="An array of single-element arrays, each containing receipt entry.")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            'example': {
                'receipt_key': 'RzSZ0BTnuG',
                'content': [['YOUR GUEST NUMBER IS'], ['43'], ['IN-N-OUT BURGER LINQ']]
            },
            'title': 'ReceiptModel',
            'description': 'A model representing a receipt with a key and its contents.',
        }


def merge_data(values):
    data = []
    for idx in range(len(values)):
        data.append([values[idx][1][0]])
        # print(data[idx])

    return data


async def store_data(data, db):
    print("Storing data...")

    key = generate_key()

    try:
        receipt = ReceiptModel(receipt_key=key, content=data)
    except ValidationError as e:
        print(f"An error occurred: {e}")
    else:
        # Convert the Pydantic model instance into a dictionary
        receipt_dict = receipt.dict()

        receipt_dict["content"] = encrypt(str(receipt_dict["content"]), base64.b64decode(secure_key))
        receipt_dict["created_at"] = datetime.datetime.utcnow()

        # Insert the dictionary into MongoDB
        result = await db["uploads"].insert_one(receipt_dict)
        print(f"Inserted document with id: {result.inserted_id}")

        return key

    return None


async def get_receipt_data(key, db):
    print(f"Getting receipt data for key: {key}")

    receipt = await db["uploads"].find_one({"receipt_key": key})
    if receipt is not None:
        await db["uploads"].delete_one({"receipt_key": key})

        receipt['content'] = decrypt(receipt['content'], base64.b64decode(secure_key))
        print(receipt['content'])

        return receipt['content']

    return None


def generate_key(length=10):
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for i in range(length))
    return key