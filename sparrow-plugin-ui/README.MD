# Sparrow ChatGPT Plugin UI - Receipt Assistant

## Description

This app implements Sparrow file upload UI functionality for Receipt Assistant ChatGPT plugin.

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
docker build --tag katanaml/sparrow-plugin-ui .
```

2. Run Docker container

```
docker run -it --name sparrow-plugin-ui -p 7860:7860 katanaml/sparrow-plugin-ui:latest
```

## Deploy to Hugging Face Spaces

1. Create new Space - https://huggingface.co/spaces

2. Clone Space repo and init Git LFS. Copy Sparrow Plugin UI files. We are using config.toml from config folder, when deploying Docker container on Hugging Face Spaces, it can't read from standard .streamlit folder

```
git lfs install
```

3. Commit and push code to Hugging Face Space, follow Space instructions. Docker container will be deployed automatically. Space example:

```
https://huggingface.co/spaces/katanaml-org/sparrow-plugin-ui
```

4. Sparrow Plugin UI will be accessible by URL, you can get it from Hugging Face Space info. For example:

```
https://katanaml-org-sparrow-plugin-ui.hf.space
```

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
