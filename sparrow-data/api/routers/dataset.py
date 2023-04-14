from fastapi import APIRouter
from datasets import load_dataset
from ast import literal_eval
from pydantic import BaseModel
from typing import Dict
from io import BytesIO
from PIL import Image
import base64
from config import settings
from huggingface_hub import login


router = APIRouter()

login(settings.huggingface_key)

class ImageResponse(BaseModel):
    image_data: str
    ground_truth_data: Dict

def encode_pil_image(image: Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode('utf-8')

@router.get("/dataset_info")
async def get_dataset_info():
    dataset = load_dataset(settings.dataset_name)

    splits = []
    for split in dataset.keys():
        split = {
            "name": split,
            "number_of_rows": len(dataset[split])
        }
        splits.append(split)

    result = {
        "dataset": settings.dataset_name,
        "splits": splits
    }

    return result


@router.get("/ground_truth", response_model=ImageResponse)
async def get_ground_truth() -> ImageResponse:
    dataset = load_dataset(settings.dataset_name)

    example = dataset['test'][0]
    image = example['image']
    encoded_img = encode_pil_image(image)

    ground_truth = example['ground_truth']
    data = literal_eval(ground_truth)['gt_parse']

    return ImageResponse(image_data=encoded_img, ground_truth_data=data)