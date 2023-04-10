from fastapi import APIRouter
from config import settings
import os
import json


router = APIRouter()


@router.get("/training",)
async def run_training():
    return {"message": "Sparrow ML training started"}


@router.get("/statistics")
async def get_statistics():
    file_path = settings.donut_training_stats_file

    # Check if the file exists, and read its content
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                content = json.load(file)
            except json.JSONDecodeError:
                content = []
    else:
        content = []

    return content