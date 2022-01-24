# Structured data extraction from scanned documents

## Description

Sparrow helps to extract and process data from scanned documents and pictures. It works with forms, invoices, receipts and other structured data.

## Instructions

1. Datasets

- [SROIE](https://www.kaggle.com/urbikn/sroie-datasetv2)

3. Build Docker image

```
docker build --tag katanaml/sparrow .
```

3. Setup remote interpreter in PyCharm

4. Run

```
python main.py
```

## Structure

```
.
├── app
│   └── layoutlmv2.py
├── main.py
├── Dockerfile
├── LICENSE
├── README.md
└── requirements.txt
```

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2021 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
