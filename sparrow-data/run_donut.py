from tools.donut.metadata_generator import DonutMetadataGenerator
from tools.donut.dataset_generator import DonutDatasetGenerator


def main():
    # Convert to sparrow format
    metadata_generator = DonutMetadataGenerator()
    metadata_generator.generate('docs/models/donut/data', "train")
    metadata_generator.generate('docs/models/donut/data', "validation")
    metadata_generator.generate('docs/models/donut/data', "test")

    # Generate dataset
    dataset_generator = DonutDatasetGenerator()
    dataset_generator.generate('docs/models/donut/data')

if __name__ == '__main__':
    main()