from tools.pdf_converter import PDFConverter
from tools.ocr_extractor import OCRExtractor


def main():
    # Convert pdf to jpg
    pdf_converter = PDFConverter()
    pdf_converter.convert_to_jpg('docs/invoices/Dataset with valid information', 'docs/invoices/data')

    # OCR
    ocr_extractor = OCRExtractor('db_resnet50', 'crnn_vgg16_bn', pretrained=True)
    ocr_extractor.extract('docs/invoices/data/invoice_0.jpg')

if __name__ == '__main__':
    main()