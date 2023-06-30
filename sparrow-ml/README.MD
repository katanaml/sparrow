# Sparrow ML

## Description

This module implements Sparrow ML model fine-tuning and inference. We are using Donut model to run document data extraction task. Fine-tuning is done using Hugging Face API.

## Install

```
pip install -r requirements.txt
```

## Usage

1. Run [**sparrow_finetuning_donut_v1.ipynb**](https://colab.research.google.com/drive/1-v1VE2Oow_klQjO-ETGyxuIP4ebIjRGC?usp=sharing) notebook to finetune Donut model on your data with **PyTorch Lighting**. This notebook shouldn't be used in MLOps pipeline, it is for research purposes.

2. Run [**sparrow_inference_donut_v1.ipynb**](https://colab.research.google.com/drive/1eCFAIst7mFOQcib3MzUdgHGpitS1sh8y?usp=sharing) notebook to test model (fine-tuned with **PyTorch Lighting**) inference. This notebook shouldn't be used in MLOps pipeline, it is for research purposes.

3. Run [**sparrow_inference_standalone_donut_v1.ipynb**](https://colab.research.google.com/drive/1OoX1llhhNWeI9j8ajJRm7dbPFA3ZlFg5?usp=sharing) notebook to test model (fine-tuned with **PyTorch Lighting**) inference with external image. This notebook shouldn't be used in MLOps pipeline, it is for research purposes.

## FastAPI Service

Set **huggingface_key** in config.py. Note down **sparrow_key** from config.py, it will be required to execute inference and training requests.

1. Run

```
cd api
```

```
uvicorn endpoints:app --workers 4
```

2. FastAPI Swagger

```
http://127.0.0.1:8000/api/v1/sparrow-ml/docs
```

**Run in Docker container**

1. Build Docker image

```
docker build --tag katanaml/sparrow-ml .
```

2. Run Docker container

```
docker run -it --name sparrow-ml -p 7860:7860 katanaml/sparrow-ml:latest
```

## Endpoints

1. Inference

```
curl -X 'POST' \
  'https://katanaml-org-sparrow-ml.hf.space/api-inference/v1/sparrow-ml/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=' \
  -F 'image_url=https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-data/docs/input/invoices/processed/images/invoice_10.jpg' \
  -F 'model_in_use=donut' \
  -F 'sparrow_key=your_key'
```

Replace URLs with your own

2. Inference statistics

```
curl -X 'GET' \
  'https://katanaml-org-sparrow-ml.hf.space/api-inference/v1/sparrow-ml/statistics' \
  -H 'accept: application/json'
```

Replace URL with your own

3. Training

```
curl -X 'POST' \
  'https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/training' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'max_epochs=30&val_check_interval=0.4&warmup_steps=81&model_in_use=donut&sparrow_key=your_key'
```

Replace URL with your own

4. Evaluate

```
curl -X 'POST' \
  'https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/evaluate' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'model_in_use=donut&sparrow_key=your_key'
```

Replace URL with your own

5. Training statistics

```
curl -X 'GET' \
  'https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/statistics/training' \
  -H 'accept: application/json'
```

Replace URL with your own

6. Evaluate statistics

```
curl -X 'GET' \
  'https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/statistics/evaluate' \
  -H 'accept: application/json'
```

Replace URL with your own

## CLI

Navigate to 'cli' folder and run 'chmod +x sparrow'. Add to system path to make it executable globally on the system.

1. Inference

```
./sparrow --api_url https://katanaml-org-sparrow-ml.hf.space/api-inference/v1/sparrow-ml/inference \
          --type inference \
          --file_path ../data/img/invoice_0.jpg \
          --model_in_use donut \
          --sparrow_key <key>
```

2. Training

```
./sparrow --api_url https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/training \
          --type training \
          --max_epochs 30 \
          --val_check_interval 0.4 \
          --warmup_steps 81 \
          --model_in_use donut \
          --sparrow_key <key>

```

3. Evaluate

```
./sparrow --api_url https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/evaluate \
          --type evaluate \
          --model_in_use donut / 
          --sparrow_key <key>
```

## Deploy to Hugging Face Spaces

1. Create new space - https://huggingface.co/spaces. Follow instructions from readme doc

2. Create huggingface_key and sparrow_key secret in space settings

3. In config.py, replace huggingface_key and sparrow_key variable with this line of code

```
huggingface_key: str = os.environ.get("huggingface_key")
```

```
sparrow_key: str = os.environ.get("sparrow_key")
```

4. Commit and push code to the space, follow readme instructions. Docker container will be deployed automatically. Example:

```
https://huggingface.co/spaces/katanaml-org/sparrow-ml
```

5. Sparrow ML API will be accessible by URL, you can get it from space info. Example:

```
https://katanaml-org-sparrow-ml.hf.space/api/v1/sparrow-ml/docs
```

## Resources

1. [Invoices Dataset for Donut v1](https://huggingface.co/datasets/katanaml-org/invoices-donut-data-v1)

2. [Invoices Model for Donut v1](https://huggingface.co/katanaml-org/invoices-donut-model-v1)

## References

1. [Transformers Tutorials](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/Donut) for Donut

2. [Document AI: Fine-tuning Donut for document-parsing using Hugging Face Transformers](https://www.philschmid.de/fine-tuning-donut) blog

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
