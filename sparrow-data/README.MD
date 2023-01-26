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

## Dataset info

- [Samples of electronic invoices](https://data.mendeley.com/datasets/tnj49gpmtz)
- [Receipts](https://www.kaggle.com/jenswalter/receipts)
- [SROIE](https://github.com/zzzDavid/ICDAR-2019-SROIE)

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
