import secrets
import string
from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError
from typing import List


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
                'array': [['YOUR GUEST NUMBER IS'], ['43'], ['IN-N-OUT BURGER LINQ']]
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
        return receipt['content']

    return None


def generate_key(length=10):
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for i in range(length))
    return key