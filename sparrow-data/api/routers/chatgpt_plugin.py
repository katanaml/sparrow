from fastapi import APIRouter, HTTPException, Response, Form
from config import settings
import os
import motor.motor_asyncio
from routers.data_utils import get_receipt_data


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

    return HTTPException(status_code=404, detail=f"No MongoDB URL provided.")


@router.post("/store_receipt")
async def run_store_receipt(chatgpt_user: str = Form(None), receipt_id: str = Form(None),
                            receipt_content: str = Form(None), sparrow_key: str = Form(None)):

    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    print(f"Storing receipt {receipt_id} for user {chatgpt_user}...")
    print(f"Receipt content: {receipt_content}")

    if "MONGODB_URL" in os.environ:
        return Response(status_code=200)

    return HTTPException(status_code=404, detail=f"No MongoDB URL provided.")