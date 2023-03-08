from datasets import load_dataset
import random


class DonutDatasetTester:
    def test(self, dataset_name):
        # Load dataset
        dataset = load_dataset(dataset_name, split="train")

        print(f"Dataset has {len(dataset)} images")
        print(f"Dataset features are: {dataset.features.keys()}")

        random_sample = random.randint(0, len(dataset) - 1)
        print(f"Random sample is {random_sample}")
        print(f"OCR text is {dataset[random_sample]['ground_truth']}")