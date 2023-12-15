# Sparrow Data OCR

## Description

This module implements OCR functionality for Sparrow ML.

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

## Plain OCR

If you want only to test how OCR works, you can run scripts in /ocr folder

1. PaddleOCR

```
python ocr_paddleocr.py
```

2. Doctr

```
python ocr_doctr.py
```

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
