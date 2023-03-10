from tools.donut.metadata_generator import DonutMetadataGenerator
from tools.donut.dataset_generator import DonutDatasetGenerator
from pathlib import Path


def main():
    # Convert to sparrow format
    base_path = 'docs/models/donut/data'
    data_dir_path = Path(base_path).joinpath("key")
    files = data_dir_path.glob("*.json")
    files_list = [file for file in files]
    # split files_list array into 3 parts, 70% train, 20% validation, 10% test
    # train_files_list = files_list[:int(len(files_list) * 0.7)]
    # validation_files_list = files_list[int(len(files_list) * 0.7):int(len(files_list) * 0.9)]
    # test_files_list = files_list[int(len(files_list) * 0.9):]

    metadata_generator = DonutMetadataGenerator()
    metadata_generator.generate(base_path, files_list, "train")
    metadata_generator.generate(base_path, files_list, "validation")
    metadata_generator.generate(base_path, files_list, "test")

    # # Generate dataset
    dataset_generator = DonutDatasetGenerator()
    dataset_generator.generate(base_path)

if __name__ == '__main__':
    main()