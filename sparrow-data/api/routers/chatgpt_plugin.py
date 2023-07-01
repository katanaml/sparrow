from fastapi import APIRouter, HTTPException, Response, Form
from config import settings
import os
import motor.motor_asyncio
from routers.data_utils import get_receipt_data
from routers.data_utils import store_receipt_db_data
from routers.data_utils import get_receipt_db_data
from routers.data_utils import delete_receipt_db_data
from routers.data_utils import get_user_receipt_db_ids
from routers.data_utils import get_user_receipt_content_db
from pymongo.errors import PyMongoError
import json


router = APIRouter()


client = None
db = None


@router.on_event("startup")
async def startup_event():
    if "MONGODB_URL" in os.environ:
        global client
        global db
        client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
        db = client.chatgpt_plugin
        print("Connected to MongoDB from ChatGPT plugin!")


@router.on_event("shutdown")
async def shutdown_event():
    if "MONGODB_URL" in os.environ:
        global client
        client.close()


@router.get("/receipt_by_id")
async def get_receipt_by_id(receipt_id: str, sparrow_key: str):
    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    if "MONGODB_URL" in os.environ:
        result = await get_receipt_data(receipt_id, db)

        if result is None:
            raise HTTPException(status_code=404, detail=f"Receipt {receipt_id} not found")

        return result

    return HTTPException(status_code=400, detail=f"No MongoDB URL provided.")


@router.post("/store_receipt_db")
async def run_store_receipt_db(chatgpt_user: str = Form(None), receipt_id: str = Form(None),
                            receipt_content: str = Form(None), sparrow_key: str = Form(None)):

    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    print(f"Storing receipt {receipt_id} for user {chatgpt_user}...")

    if "MONGODB_URL" in os.environ:
        try:
            result = await store_receipt_db_data(chatgpt_user, receipt_id, receipt_content, db)
        except PyMongoError:
            return HTTPException(status_code=400, detail=f"Saving data failed.")

        if result is not None:
            return Response(status_code=200)

    return HTTPException(status_code=400, detail=f"No MongoDB URL provided.")


@router.get("/receipt_db_by_id")
async def get_receipt_db_by_id(chatgpt_user: str, receipt_id: str, sparrow_key: str):
    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    if "MONGODB_URL" in os.environ:
        result = await get_receipt_db_data(chatgpt_user, receipt_id, db)

        if result is None:
            raise HTTPException(status_code=404, detail=f"Receipt {receipt_id} not found")

        return json.loads(result)

    return HTTPException(status_code=400, detail=f"No MongoDB URL provided.")


@router.delete("/receipt_db_by_id")
async def delete_receipt_db_by_id(chatgpt_user: str, receipt_id: str, sparrow_key: str):
    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    if "MONGODB_URL" in os.environ:
        result = await delete_receipt_db_data(chatgpt_user, receipt_id, db)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Receipt {receipt_id} not found")

        return Response(status_code=200)

    return HTTPException(status_code=400, detail=f"No MongoDB URL provided.")


@router.get("/receipt_db_ids_by_user")
async def get_receipt_db_ids_by_user(chatgpt_user: str, sparrow_key: str):
    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    if "MONGODB_URL" in os.environ:
        result = await get_user_receipt_db_ids(chatgpt_user, db)

        if result is None:
            raise HTTPException(status_code=404, detail=f"User {chatgpt_user} not found")

        return result

    return HTTPException(status_code=400, detail=f"No MongoDB URL provided.")


@router.get("/receipt_db_content_by_user")
async def get_receipt_db_content_by_user(chatgpt_user: str, sparrow_key: str):
    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    if "MONGODB_URL" in os.environ:
        result = await get_user_receipt_content_db(chatgpt_user, db)

        return result

    return HTTPException(status_code=400, detail=f"No MongoDB URL provided.")