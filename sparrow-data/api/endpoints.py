from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import dataset
from routers import ocr
from routers import chatgpt_plugin

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
app.include_router(chatgpt_plugin.router, prefix="/api-chatgpt-plugin/v1/sparrow-data", tags=["ChatGPT Plugin"])


@app.get("/")
async def root():
    return {"message": "Sparrow Data API"}