# Sparrow ML

## Description

This module implements Sparrow ML model fine-tuning and inference. We are using Donut model to run document data extraction task. Fine-tuning is done using Hugging Face API.

## Install

```
pip install -r requirements.txt
```

## Usage

1. Run **sparrow_finetuning_donut_v1.ipynb** notebook to finetune Donut model on your data with **PyTorch Lighting**. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1-v1VE2Oow_klQjO-ETGyxuIP4ebIjRGC?usp=sharing)

2. Run **sparrow_finetuning_donut_v2.ipynb** notebook to finetune Donut model on your data with **Hugging Face Trainer**. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1SxuTbM_bbnA_XKQ6rpx75mamTV6XYixF?usp=sharing)

3. Run **sparrow_inference_donut_v1.ipynb** notebook to test model (fine-tuned with **PyTorch Lighting**) inference. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1eCFAIst7mFOQcib3MzUdgHGpitS1sh8y?usp=sharing)

4. Run **sparrow_inference_standalone_donut_v1.ipynb** notebook to test model (fine-tuned with **PyTorch Lighting**) inference with external image. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1OoX1llhhNWeI9j8ajJRm7dbPFA3ZlFg5?usp=sharing)

5. Run **sparrow_inference_standalone_donut_v2.ipynb** notebook to test model (fine-tuned with **Hugging Face Trainer**) inference with external image. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1FSTh0mp99o71v2Kl_wjbbd0gHIlDQANm?usp=sharing)

## FastAPI Service

Set **huggingface_key** in config.py. Note down **sparrow_key** from config.py, it will be required to execute inference and training requests

1. Run

```
cd api
```

```
uvicorn endpoints:app --reload
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
  'http://127.0.0.1:8000/api-inference/v1/sparrow-ml/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=' \
  -F 'image_url=https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-data/docs/input/invoices/processed/images/invoice_10.jpg'
  -F 'model_in_use=donut'
  -F 'sparrow_key=2ec6602fa3fe013f3fa8859d008bd66e'
```

Replace URLs with your own

2. Inference statistics

```
curl -X 'GET' \
  'http://127.0.0.1:8000/api-inference/v1/sparrow-ml/statistics' \
  -H 'accept: application/json'
```

Replace URL with your own

3. Training

```
curl -X 'GET' \
  'http://127.0.0.1:8000/api-training/v1/sparrow-ml/training' \
  -H 'accept: application/json'
```

Replace URL with your own

4. Training statistics

```
curl -X 'GET' \
  'http://127.0.0.1:8000/api-training/v1/sparrow-ml/statistics' \
  -H 'accept: application/json'
```

Replace URL with your own

## Resources

1. [Invoices Dataset for Donut v1](https://huggingface.co/datasets/katanaml-org/invoices-donut-data-v1)

2. [Invoices Dataset for Donut v2](https://huggingface.co/datasets/katanaml-org/invoices-donut-data-v2)

3. [Invoices Model for Donut v1](https://huggingface.co/katanaml-org/invoices-donut-model-v1)

4. [Invoices Model for Donut v2](https://huggingface.co/katanaml-org/invoices-donut-model-v2)

## References

1. [Transformers Tutorials](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/Donut) for Donut

2. [Document AI: Fine-tuning Donut for document-parsing using Hugging Face Transformers](https://www.philschmid.de/fine-tuning-donut) blog

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
