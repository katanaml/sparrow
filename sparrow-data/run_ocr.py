from tools.pdf_converter import PDFConverter
from tools.ocr_extractor import OCRExtractor
import os
import shutil


def main():
    # Convert pdf to jpg
    pdf_converter = PDFConverter()
    pdf_converter.convert_to_jpg('docs/input/invoices/Dataset with valid information',
                                 'docs/input/invoices/processed/images')

    #define the source and destination directory
    src_dir = 'docs/input/invoices/processed/images'
    dst_dir = '../sparrow-ui/docs/images'

    # Get list of files in source directory
    files = os.listdir(src_dir)

    # Loop through all files in source directory and copy to destination directory
    for f in files:
        src_file = os.path.join(src_dir, f)
        dst_file = os.path.join(dst_dir, f)
        shutil.copy(src_file, dst_file)


    # OCR
    ocr_extractor = OCRExtractor('db_resnet50', 'crnn_vgg16_bn', pretrained=True)
    ocr_extractor.extract('docs/input/invoices/processed', show_prediction=False)

if __name__ == '__main__':
    main()