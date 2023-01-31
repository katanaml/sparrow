from tools.data_converter import DataConverter


def main():
    # Convert to sparrow format
    data_converter = DataConverter()
    data_converter.convert_to_sparrow_format('docs/invoices/ocr', 'docs/invoices/output')

if __name__ == '__main__':
    main()