from pathlib import Path
import random
from datasets import load_dataset


class DonutDatasetGenerator:
    def generate(self, data_dir):
        # define paths
        img_dir_path = Path(data_dir).joinpath("img")

        # Load dataset
        dataset = load_dataset("imagefolder", data_dir=img_dir_path, split="train")

        print(f"Dataset has {len(dataset)} images")
        print(f"Dataset features are: {dataset.features.keys()}")

        random_sample = random.randint(0, len(dataset) - 1)
        print(f"Random sample is {random_sample}")
        print(f"OCR text is {dataset[random_sample]['ground_truth']}")

