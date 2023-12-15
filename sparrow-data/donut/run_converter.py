from tools.data_converter import DataConverter
import os
import shutil


def main():
    # Convert to sparrow format
    data_converter = DataConverter()
    data_converter.convert_to_sparrow_format('docs/input/invoices/processed/ocr',
                                             'docs/input/invoices/processed/output')

    # define the source and destination directory
    src_dir = 'docs/input/invoices/processed/output'
    dst_dir = '../sparrow-ui/docs/json'

    # Get list of files in source directory
    files = os.listdir(src_dir)

    # Loop through all files in source directory and copy to destination directory
    for f in files:
        src_file = os.path.join(src_dir, f)
        dst_file = os.path.join(dst_dir, f)
        shutil.copy(src_file, dst_file)


if __name__ == '__main__':
    main()