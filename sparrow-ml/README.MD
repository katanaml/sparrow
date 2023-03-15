# Sparrow ML

## Description

This module implements Sparrow ML model fine-tuning and inference. We are using Donut model to run document data extraction task. Fine-tuning is done using Hugging Face API.

## Install

1. Install

```
pip install -r requirements.txt
```

## Usage

1. Run sparrow_finetuning_donut_v1.ipynb notebook to finetune Donut model on your data with **PyTorch Lighting**. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1-v1VE2Oow_klQjO-ETGyxuIP4ebIjRGC?usp=sharing)

2. Run sparrow_finetuning_donut_v2.ipynb notebook to finetune Donut model on your data with **Hugging Face Trainer**. This notebook shouldn't be used in MLOps pipeline, it is for research purposes. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1SxuTbM_bbnA_XKQ6rpx75mamTV6XYixF?usp=sharing)

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2023 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
