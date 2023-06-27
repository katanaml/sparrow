# Sparrow Data

## Description

This module implements data structure for Sparrow ML model fine-tuning. We are using list of invoices to build Hugging Face dataset.

## Install

1. Install

```
pip install -r requirements.txt
```

2. Install Poppler, required for pdf2image to work (macos example)

```
brew install poppler
```

3. Mindee docTR OCR installation with dependencies

```
pip install torch torchvision torchaudio
pip install python-doctr
```

## Usage

1. Run OCR on invoices with PDF conversion to JPG

```
python run_ocr.py
```

2. Run data conversion to Sparrow format

```
python run_converter.py
```

Run Sparrow UI to annotate the documents and create key/value pairs.

3. Run data preparation task for Donut model fine-tuning. This task will create metadata. It will create Hugging Face dataset with train, validation and test splits for Donut model fine-tuning

```
python run_donut.py
```

4. Push dataset to Huggung Face Hub. You need to have Hugging Face account and Hugging Face Hub token. Read more: https://huggingface.co/docs/datasets/main/en/image_dataset

```
python run_donut_upload.py
```

5. Test dataset by using load_dataset and fetching data from Hugging Face Hub

```
python run_donut_test.py
```

## FastAPI Service

Set **huggingface_key** in config.py

1. Run

```
cd api
```

```
uvicorn endpoints:app --workers 1
```

2. FastAPI Swagger

```
http://127.0.0.1:8000/api/v1/sparrow-data/docs
```

**Run in Docker container**

1. Build Docker image

```
docker build --tag katanaml/sparrow-data .
```

2. Run Docker container

```
docker run -it --name sparrow-data -p 7860:7860 katanaml/sparrow-data:latest
```

## Endpoints

1. Info

```
curl -X 'GET' \
  'https://katanaml-org-sparrow-data.hf.space/api-dataset/v1/sparrow-data/dataset_info' \
  -H 'accept: application/json'
```

Replace URL with your own

2. Ground truth

```
curl -X 'GET' \
  'https://katanaml-org-sparrow-data.hf.space/api-dataset/v1/sparrow-data/ground_truth' \
  -H 'accept: application/json'
```

Replace URL with your own

3. OCR service

```
curl -X 'POST' \
  'https://katanaml-org-sparrow-data.hf.space/api-ocr/v1/sparrow-data/ocr' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=' \
  -F 'image_url=https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-data/docs/input/invoices/processed/images/invoice_10.jpg' \
  -F 'post_processing=false' \
  -F 'sparrow_key=your_key'
```

Replace URL with your own

4. OCR statistics

```
curl -X 'GET' \
  'https://katanaml-org-sparrow-data.hf.space/api-ocr/v1/sparrow-data/statistics' \
  -H 'accept: application/json'
```

Replace URL with your own

5. Get OCR content for ChatGPT plugin

```
curl -X 'GET' \
  'https://katanaml-org-sparrow-data.hf.space/api-chatgpt-plugin/v1/sparrow-data/receipt_by_id/?receipt_id=your_id&sparrow_key=your_key' \
  -H 'accept: application/json'
```

Replace URL with your own

## CLI

Navigate to 'cli' folder and run 'chmod +x sparrowdata'. Add to system path to make it executable globally on the system.

1. OCR

```
./sparrowdata --api_url https://katanaml-org-sparrow-data.hf.space/api-ocr/v1/sparrow-data/ocr \
              --file_path ../docs/models/donut/data/img/test/invoice_2.jpg \
              --post_processing false \
              --sparrow_key your_key
```

## Deploy to Hugging Face Spaces

1. Create new space - https://huggingface.co/spaces. Follow instructions from readme doc

2. Create huggingface_key secret in space settings

3. In config.py, replace huggingface_key variable with this line of code

```
huggingface_key: str = os.environ.get("huggingface_key")
```

4. Commit and push code to the space, follow readme instructions. Docker container will be deployed automatically. Example:

```
https://huggingface.co/spaces/katanaml-org/sparrow-data
```

5. Sparrow Data API will be accessible by URL, you can get it from space info. Example:

```
https://katanaml-org-sparrow-data.hf.space/api/v1/sparrow-data/docs
```

## MongoDB connection

If post_processing is set to True, then OCR results will be saved to MongoDB. You need to have MongoDB Atlas account and MongoDB Atlas token. Read more: https://docs.atlas.mongodb.com/configure-api-access/

1. Set environment variable for MongoDB Atlas connection, before starting FastAPI service

```
export MONGODB_URL="mongodb+srv://sparrow:<password>@<url>/?retryWrites=true&w=majority"
```


## Dataset info

- [Samples of electronic invoices](https://data.mendeley.com/datasets/tnj49gpmtz)
- [Receipts](https://www.kaggle.com/jenswalter/receipts)
- [SROIE](https://github.com/zzzDavid/ICDAR-2019-SROIE)

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
