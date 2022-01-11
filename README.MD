# Structured data extraction from scanned documents

## Description

Sparrow helps to extract and process data from scanned documents and pictures. It works with forms, invoices, receipts and other structured data.

## Instructions

1. Install libraries

```
pip install -r requirements.txt
```

2. Run

```
python main.py
```

## Build and run container

1. Build container

```
docker build --tag katanaml/sparrow .
```

2. Run container

```
docker run -it -d --name sparrow -p 7000:7000  katanaml/sparrow:latest
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

Licensed under the Apache License, Version 2.0. Copyright 2020-2021 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/table-query-model/blob/main/LICENSE).
