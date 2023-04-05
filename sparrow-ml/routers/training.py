from fastapi import APIRouter


router = APIRouter()


@router.get("/training", tags=["training"])
async def run_training():
    return {"message": "Sparrow ML training started"}