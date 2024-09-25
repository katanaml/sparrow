from rag.agents.interface import Pipeline
from sparrow_parse.vllm.inference_factory import InferenceFactory
from sparrow_parse.extractors.vllm_extractor import VLLMExtractor
import timeit
import box
import yaml
from rich import print
from typing import Any, List
import warnings
import os


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class SparrowParsePipeline(Pipeline):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     keywords: [str],
                     query: str,
                     file_path: str,
                     index_name: str,
                     options: List[str] = None,
                     group_by_rows: bool = True,
                     update_targets: bool = True,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        # Import config vars
        with open('config.yml', 'r', encoding='utf8') as ymlfile:
            cfg = box.Box(yaml.safe_load(ymlfile))

        start = timeit.default_timer()

        query_all_data = False
        query = None
        if query_inputs[0] == "*" and query_types[0] == "*":
            query_all_data = True
            query = None

        extractor = VLLMExtractor()

        # export HF_TOKEN="hf_"
        config = {
            "method": "huggingface",  # Could be 'huggingface' or 'local_gpu'
            "hf_space": "katanaml/sparrow-qwen2-vl-7b",
            "hf_token": os.getenv('HF_TOKEN')
        }

        # Use the factory to get the correct instance
        factory = InferenceFactory(config)
        model_inference_instance = factory.get_inference_instance()

        input_data = [
            {
                "image": file_path,
                "text_input": query
            }
        ]

        # Now you can run inference without knowing which implementation is used
        result = extractor.run_inference(model_inference_instance, input_data, generic_query=query_all_data, debug=True)

        end = timeit.default_timer()

        print(f"\nJSON response:\n")
        print(result)
        print('\n')
        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")

        return result