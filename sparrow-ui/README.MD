# Sparrow UI

## Description

[Sparrow UI](https://katanaml-org-sparrow-ui.hf.space) module implements UI logic with Streamlit for document data annotation, model training/tuning and document data extraction.

#### Dashboard UI:

![Sparrow Dashboard](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/dashboard.png)

#### Annotation UI:

![Sparrow Annotation](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/annotation.png)

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

## Deploy to Hugging Face Spaces

1. Create new Space - https://huggingface.co/spaces

2. Clone Space repo and init Git LFS. Copy Sparrow UI files. We are using config.toml from config folder, when deploying Docker container on Hugging Face Spaces, it can't read from standard .streamlit folder

```
git lfs install
```

3. Add these files to LFS config

```
git lfs track "assets/ab.png"
git lfs track "docs/image/receipt_00001.png"
git lfs track "docs/image/receipt_00002.png"
git lfs track "docs/image/receipt_00003.png"
git lfs track "docs/image/w_invoice1.png"
```

4. Commit and push code to Hugging Face Space, follow Space instructions. Docker container will be deployed automatically. Space example:

```
https://huggingface.co/spaces/katanaml-org/sparrow-ui
```

5. Sparrow UI will be accessible by URL, you can get it from Hugging Face Space info. For example:

```
https://katanaml-org-sparrow-ui.hf.space
```

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2022 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
