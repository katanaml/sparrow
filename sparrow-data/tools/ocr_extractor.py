from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import json


class OCRExtractor:
    def __init__(self, det_arch, reco_arch, pretrained):
        self.model = ocr_predictor(det_arch, reco_arch, pretrained=pretrained)

    def extract(self, file_path):
        doc = DocumentFile.from_images(file_path)
        predictions = self.model(doc)

        result = predictions.export()
        print(json.dumps(result, indent=4))

        predictions.show(doc)