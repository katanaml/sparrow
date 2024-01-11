# Sparrow
Data extraction with ML and LLM

<p align="center">
  <img width="300" height="300" src="https://github.com/katanaml/sparrow/blob/main/sparrow-ui/donut/assets/sparrow_logo_5.png">
</p>

## The Principle

Sparrow is an innovative open-source solution designed for efficient data extraction and processing from various documents and images. It seamlessly handles forms, invoices, receipts, and other unstructured data sources. Sparrow stands out with its modular architecture, offering independent services such as OCR, Donut fine-tuning/inference, and a data labeling UI, all optimized for robust performance. Our current development efforts are focused on enhancing the LLM pipeline, promising exciting new features and capabilities. Our vision for Sparrow is to become the leading tool in data extraction, catering to diverse business domains. With a strong commitment to local data processing, we aim to empower customers with secure, cutting-edge technology. Join us in this journey to redefine data handling in the enterprise world.

### Services

* **[sparrow-data-donut](https://github.com/katanaml/sparrow/tree/main/sparrow-data/donut)** - This service focuses on data preparation specifically for the Donut ML model, including fine-tuning and OCR integration.
* **[sparrow-data-ocr](https://github.com/katanaml/sparrow/tree/main/sparrow-data/ocr)** - A standalone OCR service, providing robust optical character recognition as part of the Sparrow suite.
* **[sparrow-ml-donut](https://github.com/katanaml/sparrow/tree/main/sparrow-ml/donut)** - Dedicated to the Donut ML model, this service handles both fine-tuning and inference, streamlining the machine learning workflow.
* **[sparrow-ml-lemming](https://github.com/katanaml/sparrow/tree/main/sparrow-ml/lemming)** - A specialized service for the LLM RAG pipeline, enhancing the capabilities of language model processing.
* **[sparrow-ui-donut](https://github.com/katanaml/sparrow/tree/main/sparrow-ui/donut)** - A user-friendly interface for managing Donut ML model data labeling services and a dashboard.

Summary:

- **For LLM RAG Enthusiasts** - Opt for the `lemming` service, specifically designed to cater to your needs in LLM RAG applications.
- **For Traditional ML Implementations** - The `donut` service is available for those seeking machine learning solutions independent of LLM.

Sparrow offers a diverse range of services, as outlined previously. Our current developmental focus is primarily on enhancing and expanding the capabilities of the `lemming` service.

## Installation

### Lemming

1. Install Weaviate local DB with Docker:
   
```
docker compose up -d
```

2. Install the requirements: 

```
pip install -r requirements.txt
```

3. Install <a href="https://ollama.ai">Ollama</a> and pull LLM model specified in config.yml

### Donut

### OCR

## Usage

## Examples

### Inference with Donut ML model

![Inference Results](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/donut/assets/inference_actual.png)

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2024 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
