# Sparrow
Data extraction with ML and LLM

<p align="center">
  <img width="300" height="300" src="https://github.com/katanaml/sparrow/blob/main/sparrow-ui/donut/assets/sparrow_logo_5.png">
</p>

## The Principle

Sparrow is an innovative open-source solution designed for efficient data extraction and processing from various documents and images. It seamlessly handles forms, invoices, receipts, and other unstructured data sources. Sparrow stands out with its modular architecture, offering independent services such as OCR, Donut fine-tuning/inference, and a data labeling UI, all optimized for robust performance. Our current development efforts are focused on enhancing the LLM pipeline, promising exciting new features and capabilities. Our vision for Sparrow is to become the leading tool in data extraction, catering to diverse business domains. With a strong commitment to local data processing, we aim to empower customers with secure, cutting-edge technology. Join us in this journey to redefine data handling in the enterprise world.

### Modules

* **[sparrow-data](https://github.com/katanaml/sparrow/tree/main/sparrow-data/donut)** - Sparrow Data service. Data preparation for Donut ML model fine-tuning and OCR
* **[sparrow-data](https://github.com/katanaml/sparrow/tree/main/sparrow-data/ocr)** - Sparrow Data OCR service. Standalone OCR implementation
* **[sparrow-ml](https://github.com/katanaml/sparrow/tree/main/sparrow-ml/donut)** - Sparrow ML service for Donut ML model fine-tuning and inference
* **[sparrow-ml](https://github.com/katanaml/sparrow/tree/main/sparrow-ml/donut)** - Sparrow ML service for LLM RAG pipeline
* **[sparrow-ui](https://github.com/katanaml/sparrow/tree/main/sparrow-ui/donut)** - Sparrow UI service. UI for Donut ML model services and dashboard UI for LLM RAG

## Installation

## Usage

## Examples

### Inference with Donut ML model

![Inference Results](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/donut/assets/inference_actual.png)

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2024 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
