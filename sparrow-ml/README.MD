# Sparrow ML

## Description

This module implements Sparrow ML model fine-tuning and inference. We are using Donut model to run document data extraction task. Fine-tuning is done using Hugging Face API.

## Install

1. Install

```
pip install -r requirements.txt
```

## Usage

1. Run **sparrow_finetuning_donut_v1.ipynb** notebook to finetune Donut model on your data with **PyTorch Lighting**. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1-v1VE2Oow_klQjO-ETGyxuIP4ebIjRGC?usp=sharing)

2. Run **sparrow_finetuning_donut_v2.ipynb** notebook to finetune Donut model on your data with **Hugging Face Trainer**. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1SxuTbM_bbnA_XKQ6rpx75mamTV6XYixF?usp=sharing)

3. Run **sparrow_inference_donut_v1.ipynb** notebook to test model (fine-tuned with **PyTorch Lighting**) inference. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1eCFAIst7mFOQcib3MzUdgHGpitS1sh8y?usp=sharing)

4. Run **sparrow_inference_standalone_donut_v1.ipynb** notebook to test model (fine-tuned with **PyTorch Lighting**) inference with external image. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1OoX1llhhNWeI9j8ajJRm7dbPFA3ZlFg5?usp=sharing)

5. Run **sparrow_inference_standalone_donut_v2.ipynb** notebook to test model (fine-tuned with **Hugging Face Trainer**) inference with external image. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1FSTh0mp99o71v2Kl_wjbbd0gHIlDQANm?usp=sharing)

## Resources

1. [Invoices Dataset for Donut v1](https://huggingface.co/datasets/katanaml-org/invoices-donut-data-v1)

2. [Invoices Dataset for Donut v2](https://huggingface.co/datasets/katanaml-org/invoices-donut-data-v2)

3. [Invoices Model for Donut v1](https://huggingface.co/katanaml-org/invoices-donut-model-v1)

4. [Invoices Model for Donut v2](https://huggingface.co/katanaml-org/invoices-donut-model-v2)

## References

1. [Transformers Tutorials](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/Donut) for Donut

2. [Document AI: Fine-tuning Donut for document-parsing using Hugging Face Transformers](https://www.philschmid.de/fine-tuning-donut) blog

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
