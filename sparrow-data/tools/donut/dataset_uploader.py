from pathlib import Path
from datasets import load_dataset

class DonutDatasetUploader:
    def upload(self, data_dir):
        # define paths
        img_dir_path = Path(data_dir).joinpath("img")

        dataset = load_dataset("imagefolder", data_dir=img_dir_path)

        # Save dataset: https://huggingface.co/docs/datasets/main/en/image_dataset
        dataset.push_to_hub("katanaml-org/invoices-donut-data-v1", private=True)

