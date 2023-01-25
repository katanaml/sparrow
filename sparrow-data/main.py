from tools.pdf_converter import PDFConverter


def main():
    # Convert pdf to jpg
    pdf_converter = PDFConverter()
    pdf_converter.convert_to_jpg('docs/invoices/Dataset with valid information', 'docs/invoices/data')

    # OCR


if __name__ == '__main__':
    main()