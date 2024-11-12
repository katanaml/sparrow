from gradio_client import Client, handle_file
from sparrow_parse.vllm.inference_base import ModelInference
import json


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


    def inference(self, input_data, mode=None):
        if mode == "static":
            simple_json = self.get_simple_json()
            return simple_json

        client = Client(self.hf_space, hf_token=self.hf_token)

        result = client.predict(
            image=handle_file(input_data[0]["file_path"]),
            text_input=input_data[0]["text_input"],
            api_name="/run_inference"
        )

        return self.process_response(result)
