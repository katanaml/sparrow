import argparse
import os
import sys
import json
from ocr import ocr_call


def ocr(api_url, file_path, sparrow_key):
    result = ocr_call(api_url, file_path, sparrow_key)
    pretty_result = json.dumps(json.loads(result), indent=4)
    print(pretty_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sparrow OCR CLI')
    parser.add_argument('-a', '--api_url', type=str, required=True, help='API URL')
    parser.add_argument('-f', '--file_path', type=str, help='File path')
    parser.add_argument('-p', '--post_processing', type=bool, help='Post processing')
    parser.add_argument('-k', '--sparrow_key', type=str, required=True, help='Sparrow key')

    args = parser.parse_args()

    api_url = args.api_url
    file_path = args.file_path
    post_processing = args.post_processing
    sparrow_key = args.sparrow_key

    if not os.path.exists(file_path):
        print("File does not exist")
        sys.exit(1)

    ocr(api_url, file_path, post_processing, sparrow_key)