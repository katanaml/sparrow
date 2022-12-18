# Sparrow UI

## Description

Sparrow UI module implements UI logic with Streamlit for document data annotation, model training/tuning and document data extraction.

![Sparrow Dashboard](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/dashboard.png)

## Instructions

1. Install

Streamlit docs:
https://docs.streamlit.io/library/get-started/installation

```
pip install -r requirements.txt
```

2. Run

```
streamlit run main.py
```

## Run in Docker container

1. Build Docker image

```
docker build --tag katanaml/sparrow-ui .
```

2. Run Docker container

```
docker run -it --name sparrow-ui -p 7860:7860 katanaml/sparrow-ui:latest
```


## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2021 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
