from fastapi import APIRouter


router = APIRouter()


@router.get("/training",)
async def run_training():
    return {"message": "Sparrow ML training started"}


@router.get("/statistics")
async def get_statistics():
    return {"message": "Training statistics"}