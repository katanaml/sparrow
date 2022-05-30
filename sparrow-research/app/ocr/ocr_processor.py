import easyocr
import PIL
from PIL import Image
from PIL import ImageDraw


def draw_boxes(image, bounds, color='yellow', width=2):
    draw = ImageDraw.Draw(image)
    for bound in bounds:
        p0, p1, p2, p3 = bound[0]
        draw.line([*p0, *p1, *p2, *p3, *p0], fill=color, width=width)
    return image


def main(image):
    with open(image, 'rb') as f:
        img = f.read()
    reader = easyocr.Reader(['en'])
    result = reader.readtext(img)

    im = PIL.Image.open(image)
    draw_boxes(im, result)
    im.save('../../docs/result.jpg')


if __name__ == "__main__":
    image = '../../docs/invoice.jpg'
    main(image)
