from app.layoutlmv2 import process_document
from PIL import Image, ImageDraw, ImageFont


def main():
    image = Image.open('docs/invoice.jpg')
    process_document(image)


if __name__ == "__main__":
    main()
