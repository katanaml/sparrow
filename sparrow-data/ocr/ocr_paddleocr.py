from paddleocr import PaddleOCR, draw_ocr
import cv2
from PIL import Image
from tqdm import tqdm
import os


model = PaddleOCR(use_angle_cls=True, lang='fr')


# Function to read an image from a file path and run OCR
def ocr_image(image_path):
    # Use OpenCV to read the image
    image = cv2.imread(image_path)
    # Convert the image from BGR to RGB (PaddleOCR expects RGB)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Run OCR on the image
    result = model.ocr(image, cls=True)
    return image, result


def main():
    docs_in_path = 'docs/input/'
    docs_out_path = 'docs/output/'

    for data_file in tqdm(sorted((f for f in os.listdir(docs_in_path) if not f.startswith(".")), key=str.lower)):
        image_path = docs_in_path + data_file

        image, result = ocr_image(image_path)

        # write the result to a json file
        with open(docs_out_path + data_file.replace('.jpg', '') + '.txt', 'w', encoding='utf-8') as file:
            for idx in range(len(result)):
                res = result[idx]
                for line in res:
                    line_text = line[1][0]
                    file.write(line_text + '\n')

                # Visualize the results
                image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                boxes = [line[0] for line in res]  # Extract the bounding boxes
                txts = [line[1][0] for line in res]  # Extract the recognized texts
                scores = [line[1][1] for line in res if
                          isinstance(line[1][1], float)]  # Ensure scores are floats

                # Now we use the draw_ocr function, passing the boxes, texts, and scores
                # Replace font path
                im_show = draw_ocr(image, boxes, txts, scores, font_path='/System/Library/Fonts/Supplemental/Arial.ttf')
                im_show = Image.fromarray(im_show)

                # Save the visualized image
                vis_image_path = docs_out_path + data_file
                im_show.save(vis_image_path)

        # break


if __name__ == '__main__':
    main()