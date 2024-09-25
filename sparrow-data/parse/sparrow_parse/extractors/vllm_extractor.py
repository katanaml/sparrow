from sparrow_parse.vllm.inference_factory import InferenceFactory
from rich import print
import os


class VLLMExtractor(object):
    def __init__(self):
        pass

    def run_inference(self, model_inference_instance, input_data, generic_query=False, debug=False):
        if generic_query:
            input_data[0]["text_input"] = "retrieve document data. return response in JSON format"

        if debug:
            print("Input Data:", input_data)

        result = model_inference_instance.inference(input_data)

        return result

if __name__ == "__main__":
    extractor = VLLMExtractor()

    # export HF_TOKEN="hf_"
    config = {
        "method": "huggingface",  # Could be 'huggingface' or 'local_gpu'
        "hf_space": "katanaml/sparrow-qwen2-vl-7b",
        "hf_token": os.getenv('HF_TOKEN'),
        # Additional fields for local GPU inference
        # "device": "cuda", "model_path": "model.pth"
    }

    # Use the factory to get the correct instance
    factory = InferenceFactory(config)
    model_inference_instance = factory.get_inference_instance()

    input_data = [
        {
            "image": "/Users/andrejb/Documents/work/epik/bankstatement/bonds_table.png",
            "text_input": "retrieve financial instruments data. return response in JSON format"
        }
    ]

    # Now you can run inference without knowing which implementation is used
    result = extractor.run_inference(model_inference_instance, input_data, generic_query=False, debug=True)
    print("Inference Result:", result)