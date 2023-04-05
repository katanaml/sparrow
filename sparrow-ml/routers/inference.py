from fastapi import APIRouter


router = APIRouter()


@router.get("/inference", tags=["inference"])
async def run_inference():
    return {"message": "Sparrow ML inference call"}