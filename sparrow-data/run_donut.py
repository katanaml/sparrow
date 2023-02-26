from tools.donut.metadata_generator import MetadataGenerator


def main():
    # Convert to sparrow format
    metadata_generator = MetadataGenerator()
    metadata_generator.generate('docs/models/donut/data')

if __name__ == '__main__':
    main()