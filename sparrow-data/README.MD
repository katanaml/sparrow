# Sparrow Data

## Description

This module implements data structure for Sparrow ML model fine-tuning. We are using list of invoices to build Hugging Face dataset. This dataset is used for Donut model fine-tuning.

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

## Dataset info

- [Samples of electronic invoices](https://data.mendeley.com/datasets/tnj49gpmtz)
- [Receipts](https://www.kaggle.com/jenswalter/receipts)
- [SROIE](https://github.com/zzzDavid/ICDAR-2019-SROIE)

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
