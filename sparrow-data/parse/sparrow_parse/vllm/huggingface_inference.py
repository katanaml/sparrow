from gradio_client import Client, handle_file
from sparrow_parse.vllm.inference_base import ModelInference


class HuggingFaceInference(ModelInference):
    def __init__(self, hf_space, hf_token):
        self.hf_space = hf_space
        self.hf_token = hf_token

    def inference(self, input_data):
        client = Client(self.hf_space, hf_token=self.hf_token)

        result = client.predict(
            image=handle_file(input_data[0]["image"]),
            text_input=input_data[0]["text_input"],
            api_name="/run_inference"
        )

        return result
