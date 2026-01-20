from gradio_client import Client, handle_file
from sparrow_parse.vllm.inference_base import ModelInference
import json
import os
import ast


class HuggingFaceInference(ModelInference):
    def __init__(self, hf_space, hf_token):
        self.hf_space = hf_space
        self.hf_token = hf_token


    def process_response(self, output_text):
        json_string = output_text

        json_string = json_string.strip("[]'")
        json_string = json_string.replace("```json\n", "").replace("\n```", "")
        json_string = json_string.replace("'", "")

        try:
            formatted_json = json.loads(json_string)
            return json.dumps(formatted_json, indent=2)
        except json.JSONDecodeError as e:
            print("Failed to parse JSON:", e)
            return output_text


    def inference(self, input_data, apply_annotation=False, ocr_callback=None, mode=None):
        if mode == "static":
            simple_json = self.get_simple_json()
            return [simple_json]

        client = Client(self.hf_space, hf_token=self.hf_token)

        # Extract and prepare the absolute paths for all file paths in input_data
        file_paths = [
            os.path.abspath(file_path)
            for data in input_data
            for file_path in data["file_path"]
        ]

        # Validate file existence and prepare files for the Gradio client
        image_files = [handle_file(path) for path in file_paths if os.path.exists(path)]

        results = client.predict(
            input_imgs=image_files,
            text_input=input_data[0]["text_input"],  # Single shared text input for all images
            api_name="/run_inference"  # Specify the Gradio API endpoint
        )

        # Convert the string into a Python list
        parsed_results = ast.literal_eval(results)

        results_array = []
        for page_output in parsed_results:
            page_result = self.process_response(page_output)
            results_array.append(page_result)

        return results_array