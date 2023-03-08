from tools.donut.dataset_uploader import DonutDatasetUploader

def main():
    dataset_uploader = DonutDatasetUploader()
    dataset_uploader.upload('docs/models/donut/data')

if __name__ == '__main__':
    main()