# Sparrow Parse

## Description

This module implements Sparrow Parse [library](https://pypi.org/project/sparrow-parse/) library with helpful methods for data pre-processing, parsing and extracting information. Library relies on Visual LLM functionality, Table Transformers and is part of Sparrow. Check main [README](https://github.com/katanaml/sparrow)

## Install

```
pip install sparrow-parse
```

## Parsing and extraction

### Sparrow Parse VL LLM extractor with local MLX or Hugging Face Cloud GPU infra

Supports text based instruction calling

```
# run locally: python -m sparrow_parse.extractors.vllm_extractor

from sparrow_parse.vllm.inference_factory import InferenceFactory
from sparrow_parse.extractors.vllm_extractor import VLLMExtractor

# export HF_TOKEN="hf_"
config = {
    "method": "mlx",  # Could be 'huggingface', 'mlx' or 'local_gpu'
    "model_name": "mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit",
    # "hf_space": "katanaml/sparrow-qwen2-vl-7b",
    # "hf_token": os.getenv('HF_TOKEN'),
    # Additional fields for local GPU inference
    # "device": "cuda", "model_path": "model.pth"
}
    
# Use the factory to get the correct instance
factory = InferenceFactory(config)
model_inference_instance = factory.get_inference_instance()

input_data = [
    {
        "file_path": "sparrow_parse/images/bonds_table.png",
        "text_input": "retrieve [{\"instrument_name\":\"str\", \"valuation\":\"int\"}]. return response in JSON format"
    }
]

# input_data = [
#     {
#         "file_path": None,
#         "text_input": "why earth is spinning around the sun?"
#     }
# ]

# Now you can run inference without knowing which implementation is used
results_array, num_pages = extractor.run_inference(model_inference_instance, input_data, tables_only=False,
                                                   generic_query=False,
                                                   crop_size=0,
                                                   apply_annotation=False,
                                                   debug_dir="/Users/andrejb/Work/katana-git/sparrow/sparrow-ml/llm/data/",
                                                   debug=True,
                                                   mode=None)

for i, result in enumerate(results_array):
    print(f"Result for page {i + 1}:", result)
print(f"Number of pages: {num_pages}")
```

Use `tables_only=True` if you want to extract only tables.

Use `crop_size=N` (where `N` is an integer) to crop N pixels from all borders of the input images. This can be helpful for removing unwanted borders or frame artifacts from scanned documents.

Use `mode="static"` if you want to simulate LLM call, without executing LLM backend.

Use 'apply_annotation=True' to apply box annotations for structured data extraction

Method `run_inference` will return results and number of pages processed.

To run with Hugging Face backend use these config values:

```
config = {
    "method": "huggingface",
    "hf_space": "katanaml/sparrow-qwen2-vl-7b",
    "hf_token": os.getenv('HF_TOKEN'),
}
```

Note: GPU backend `katanaml/sparrow-qwen2-vl-7b` is private, to be able to run below command, you need to create your own backend on Hugging Face space using [code](https://github.com/katanaml/sparrow/tree/main/sparrow-data/parse/sparrow_parse/vllm/infra/qwen2_vl_7b) from Sparrow Parse.

## PDF pre-processing

```
from sparrow_parse.extractor.pdf_optimizer import PDFOptimizer

pdf_optimizer = PDFOptimizer()

num_pages, output_files, temp_dir = pdf_optimizer.split_pdf_to_pages(file_path,
                                                                     debug_dir,
                                                                     convert_to_images)

```

Example:

*file_path* - `/data/invoice_1.pdf`

*debug_dir* - set to not `None`, for debug purposes only

*convert_to_images* - default `False`, to split into PDF files

## Image cropping

```
from sparrow_parse.helpers.image_optimizer import ImageOptimizer

image_optimizer = ImageOptimizer()

cropped_file_path = image_optimizer.crop_image_borders(file_path, temp_dir, debug_dir, crop_size)
```

Example:

*file_path* - `/data/invoice_1.jpg`

*temp_dir* - directory to store cropped files

*debug_dir* - set to not `None`, for debug purposes only

*crop_size* - Number of pixels to crop from each border

## Library build

Create Python virtual environment

```
python -m venv .env_sparrow_parse
```

Install Python libraries

```
pip install -r requirements.txt
```

Build package

```
pip install setuptools wheel
python setup.py sdist bdist_wheel
```

Upload to PyPI

```
pip install twine
twine upload dist/*
```

## Commercial usage

Sparrow is available under the GPL 3.0 license, promoting freedom to use, modify, and distribute the software while ensuring any modifications remain open source under the same license. This aligns with our commitment to supporting the open-source community and fostering collaboration.

Additionally, we recognize the diverse needs of organizations, including small to medium-sized enterprises (SMEs). Therefore, Sparrow is also offered for free commercial use to organizations with gross revenue below $5 million USD in the past 12 months, enabling them to leverage Sparrow without the financial burden often associated with high-quality software solutions.

For businesses that exceed this revenue threshold or require usage terms not accommodated by the GPL 3.0 license—such as integrating Sparrow into proprietary software without the obligation to disclose source code modifications—we offer dual licensing options. Dual licensing allows Sparrow to be used under a separate proprietary license, offering greater flexibility for commercial applications and proprietary integrations. This model supports both the project's sustainability and the business's needs for confidentiality and customization.

If your organization is seeking to utilize Sparrow under a proprietary license, or if you are interested in custom workflows, consulting services, or dedicated support and maintenance options, please contact us at abaranovskis@redsamuraiconsulting.com. We're here to provide tailored solutions that meet your unique requirements, ensuring you can maximize the benefits of Sparrow for your projects and workflows.

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the GPL 3.0. Copyright 2020-2025 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
