import os
import json
import math


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

                            len_x = dimensions[1]
                            len_y = dimensions[0]
                            (x1, y1) = word['geometry'][0]
                            (x2, y2) = word['geometry'][1]
                            x1 = math.floor(x1 * len_x)
                            y1 = math.floor(y1 * len_y)
                            x2 = math.ceil(x2 * len_x)
                            y2 = math.ceil(y2 * len_y)

                            word_data = {
                                "value": word['value'],
                                "label": "",
                                "rect": {
                                    "x1": x1,
                                    "y1": y1,
                                    "x2": x2,
                                    "y2": y2
                                }
                            }
                            annotations_json['words'].append(word_data)

                with open(output_file, 'w') as f:
                    json.dump(annotations_json, f, indent=2)

            file_id += 1

