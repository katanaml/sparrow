from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import os
from tqdm import tqdm


def main():
    model = ocr_predictor('db_resnet50', 'crnn_vgg16_bn', pretrained=True)
    docs_in_path = 'docs/input/'
    docs_out_path = 'docs/output/'

    for data_file in tqdm(sorted((f for f in os.listdir(docs_in_path) if not f.startswith(".")), key=str.lower)):
        doc = DocumentFile.from_images(docs_in_path + data_file)
        predictions = model(doc)

        # write the result to a json file
        with open(docs_out_path + data_file.replace('.jpg', '') + '.txt', 'w', encoding='utf-8') as file:
            # Iterate through the result pages
            for page in predictions.pages:
                # Within each page, iterate through the blocks
                for block in page.blocks:
                    # Each block can have several lines
                    for line in block.lines:
                        # Each line contains a list of words
                        line_text = ' '.join([word.value for word in line.words])
                        file.write(line_text + '\n')
                    # Optionally add an extra newline to separate blocks of text
                    file.write('\n')

        # display bounding boxes
        predictions.show(doc)


if __name__ == '__main__':
    main()