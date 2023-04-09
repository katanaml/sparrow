from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import donut_inference, donut_training

app = FastAPI(openapi_url="/api/v1/sparrow-ml/openapi.json", docs_url="/api/v1/sparrow-ml/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(donut_inference.router, prefix="/api-inference/v1/sparrow-ml", tags=["Donut Inference"])
app.include_router(donut_training.router, prefix="/api-training/v1/sparrow-ml", tags=["Donut Training"])


@app.get("/")
async def root():
    return {"message": "Sparrow ML API"}