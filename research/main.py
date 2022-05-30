# from app.layoutlmv2 import process_document
# from app.layoutlmv2_cord_train import process_document
# from app.layoutlmv2_cord_evaluate import process_document
# from app.layoutlmv2_cord_train_hf import process_document
from research.app.layoutlmv2_cord_inference import process_document
from PIL import Image


def main():
    image = Image.open('docs/invoice.jpg').convert('RGB')
    image = process_document(image)
    image.save('docs/invoice_processed.jpg')

if __name__ == "__main__":
    main()
