from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import dataset
from routers import ocr

app = FastAPI(openapi_url="/api/v1/sparrow-data/openapi.json", docs_url="/api/v1/sparrow-data/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(dataset.router, prefix="/api-dataset/v1/sparrow-data", tags=["Dataset"])
app.include_router(ocr.router, prefix="/api-ocr/v1/sparrow-data", tags=["OCR"])


@app.get("/")
async def root():
    return {"message": "Sparrow Data API"}