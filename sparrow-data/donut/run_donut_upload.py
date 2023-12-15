from tools.donut.dataset_uploader import DonutDatasetUploader

def main():
    dataset_uploader = DonutDatasetUploader()
    dataset_uploader.upload('docs/models/donut/data', "katanaml-org/invoices-donut-data-v1")

if __name__ == '__main__':
    main()