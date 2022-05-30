from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import json

model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
image = DocumentFile.from_images("docs/1014-receipt.jpg")

result = model(image)

result_json = result.export()
print(json.dumps(result_json, indent=4))

result.show(image)
