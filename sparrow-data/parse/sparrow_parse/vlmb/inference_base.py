from abc import ABC, abstractmethod
import json


class ModelInference(ABC):
    @abstractmethod
    def inference(self, input_data, apply_annotation=False, ocr_callback=None, mode=None):
        """This method should be implemented by subclasses."""
        pass

    def get_simple_json(self):
        # Define a simple data structure
        data = {
          "table": [
                {
                  "description": "Revenues",
                  "latest_amount": 12453,
                  "previous_amount": 11445
                },
                {
                  "description": "Operating expenses",
                  "latest_amount": 9157,
                  "previous_amount": 8822
                }
            ]
        }

        # Convert the dictionary to a JSON string
        json_data = json.dumps(data, indent=4)
        return json_data
