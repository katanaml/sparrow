from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import json
import os
from tqdm import tqdm


class OCRExtractor:
    def __init__(self, det_arch, reco_arch, pretrained):
        self.model = ocr_predictor(det_arch, reco_arch, pretrained=pretrained)

    def extract(self, file_path, show_prediction=False):
        data_path = file_path + '/images/'
        ocr_path = file_path + '/ocr/'

        for data_file in tqdm(sorted((f for f in os.listdir(data_path) if not f.startswith(".")), key=str.lower)):
            doc = DocumentFile.from_images(data_path + data_file)
            predictions = self.model(doc)

            result = predictions.export()
            # write the result to a json file
            with open(ocr_path + data_file.replace('.jpg', '') + '.json', 'w') as f:
                json.dump(result, f, indent=4)

            if show_prediction:
                predictions.show(doc)
                break
