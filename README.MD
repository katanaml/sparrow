# Structured data extraction from scanned documents

## Description

Sparrow helps to extract and process data from scanned documents and pictures. It works with forms, invoices, receipts and other structured data.

## Instructions (for research folder)

1. Build Docker image

```
docker build --tag katanaml/sparrow .
```

2. Run

```
python main.py
```

## Resources

1. CORD dataset Hugging Face builder [class](https://github.com/katanaml/sparrow/blob/main/research/app/cord/cord.py)

2. LayoutLMv2 model fine [tuning](https://github.com/katanaml/sparrow/blob/main/research/app/Fine_tuning_LayoutLMv2ForTokenClassification_on_CORD_using_HuggingFace_Trainer_ipynb.ipynb) with CORD dataset using Hugging Face Trainer [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1AtbMQFw_ahESLYVsHdoYg-NZrL9i2evB?usp=sharing)

3. LayoutLMv2 model fine [tuning](https://github.com/katanaml/sparrow/blob/main/research/app/Fine_tuning_LayoutLMv2ForTokenClassification_on_CORD.ipynb) with CORD dataset using PyTorch and Transformers [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DvN9rJPpTC5-9V76DGVRmb3cYu3lvaHO?usp=sharing)

4. LayoutXLM model fine [tuning](https://colab.research.google.com/drive/16bKTkih-SkuE8Ckbp3rOpJ8p8paAVzrw?usp=sharing) with CORD dataset using PyTorch and Transformers

5. LayoutLMv2 [inference](https://github.com/katanaml/sparrow/blob/main/research/app/Inference_with_LayoutLMv2ForTokenClassification_CORD.ipynb), trained with CORD dataset [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1zx1awZB9BbBCKPddvMK7tR1i4iN_wGrO?usp=sharing)

6. LayoutLMv2 true [inference](https://github.com/katanaml/sparrow/blob/main/research/app/True_Inference_with_LayoutLMv2ForTokenClassification_CORD.ipynb), trained with CORD dataset [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1g1b5gSaOr4awkILH6yOr1p1z2HrBPPNf?usp=sharing)

7. LayoutLMv2 Gradio demo [app](https://github.com/katanaml/sparrow/blob/main/research/app/Gradio_LayoutLMv2ForTokenClassification_CORD.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1nhC3NGCQz46-SXar-N9m5Wr-iNwO7s6k?usp=sharing)

8. [Transformers-Tutorials](https://github.com/NielsRogge/Transformers-Tutorials)

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2021 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
