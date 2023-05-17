from fastapi import APIRouter, Form, BackgroundTasks
from config import settings
import os
import json
from routers.donut_evaluate import run_evaluate_donut
from routers.donut_training import run_training_donut
import utils


router = APIRouter()


def invoke_training(max_epochs, val_check_interval, warmup_steps, model_in_use, sparrow_key):
    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    if model_in_use == 'donut':
        processing_time = run_training_donut(max_epochs, val_check_interval, warmup_steps)
        print(f"Processing time training: {processing_time:.2f} seconds")


@router.post("/training")
async def run_training(background_tasks: BackgroundTasks,
                       max_epochs: int = Form(30),
                       val_check_interval: float = Form(0.4),
                       warmup_steps: int = Form(81),
                       model_in_use: str = Form('donut'),
                       sparrow_key: str = Form(None)):

    background_tasks.add_task(invoke_training, max_epochs, val_check_interval, warmup_steps, model_in_use, sparrow_key)

    return {"message": "Sparrow ML training started in the background"}


def invoke_evaluate(model_in_use, sparrow_key):
    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    if model_in_use == 'donut':
        scores, accuracy, processing_time = run_evaluate_donut()
        utils.log_stats(settings.evaluate_stats_file, [processing_time, scores, accuracy, settings.model])
        print(f"Processing time evaluate: {processing_time:.2f} seconds")


@router.post("/evaluate")
async def run_evaluate(background_tasks: BackgroundTasks,
                       model_in_use: str = Form('donut'),
                       sparrow_key: str = Form(None)):

    background_tasks.add_task(invoke_evaluate, model_in_use, sparrow_key)

    return {"message": "Sparrow ML model evaluation started in the background"}


@router.get("/statistics")
async def get_statistics():
    file_path = settings.training_stats_file

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