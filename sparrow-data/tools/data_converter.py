import os
import json


class DataConverter:
    def convert_to_sparrow_format(self, data_path, output_path):
        file_id = 0
        for ocr_file in sorted((f for f in os.listdir(data_path) if not f.startswith(".")), key=str.lower):
            output_file = output_path + '/' + ocr_file
            # convert the ocr file to sparrow format
            with open(data_path + '/' + ocr_file, 'r') as f:
                ocr_data = json.load(f)
                page = ocr_data['pages'][0]
                dimensions = page['dimensions']

                annotations_json = {
                    "meta": {
                        "version": "v0.1",
                        "split": "-",
                        "image_id": file_id,
                        "image_size": {
                            "width": dimensions[1],
                            "height": dimensions[0]
                        }
                    },
                    "words": []
                }

                for block in page['blocks']:
                    for line in block['lines']:
                        for word in line['words']:
                            word_data = {
                                "value": word['value'],
                                "label": "",
                                "rect": {
                                    "x1": word['geometry'][0][0],
                                    "y1": word['geometry'][0][1],
                                    "x2": word['geometry'][1][0],
                                    "y2": word['geometry'][1][1]
                                }
                            }
                            annotations_json['words'].append(word_data)

                with open(output_file, 'w') as f:
                    json.dump(annotations_json, f, indent=2)

            file_id += 1

