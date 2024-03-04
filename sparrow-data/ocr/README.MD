# Sparrow Data OCR

## Description

This module implements OCR functionality for Sparrow.

## Install

1. Install

```
pip install -r requirements.txt
```

## Sparrow OCR

If you want to test how OCR works, you can run this API request through CURL

```
curl -X 'POST' \
  'http://127.0.0.1:8001/api/v1/sparrow-ocr/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=' \
  -F 'image_url=https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-ml/llm/data/inout-20211211_001.jpg'
```

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2024 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
