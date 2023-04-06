from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import inference, training

app = FastAPI(openapi_url="/api/v1/sparrow-ml/openapi.json", docs_url="/api/v1/sparrow-ml/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(inference.router, prefix="/api/v1/sparrow-ml")
app.include_router(training.router, prefix="/api/v1/sparrow-ml")


@app.get("/")
async def root():
    return {"message": "Sparrow ML API"}