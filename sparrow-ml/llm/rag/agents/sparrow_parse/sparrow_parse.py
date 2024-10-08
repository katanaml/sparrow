from rag.agents.interface import Pipeline
from sparrow_parse.vllm.inference_factory import InferenceFactory
from sparrow_parse.extractors.vllm_extractor import VLLMExtractor
import timeit
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Any, List
from .sparrow_validator import Validator
from .sparrow_utils import is_valid_json, get_json_keys_as_string
import warnings
import os


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class SparrowParsePipeline(Pipeline):

    def __init__(self):
        pass

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

        start = timeit.default_timer()

        query_all_data = False
        if query == "*":
            query_all_data = True
            query = None
        else:
            try:
                query, query_schema = self.invoke_pipeline_step(lambda: self.prepare_query_and_schema(query, debug),
                                                          "Preparing query and schema", local)
            except ValueError as e:
                return str(e)

        llm_output = self.invoke_pipeline_step(lambda: self.execute_query(options, query_all_data, query, file_path, debug),
                                               "Executing query", local)

        validation_result = None
        if query_all_data is False:
            validation_result = self.invoke_pipeline_step(lambda: self.validate_result(llm_output, query_all_data, query_schema, debug),
                                                      "Validating result", local)

        end = timeit.default_timer()

        print(f"Time to retrieve answer: {end - start}")

        return validation_result if validation_result is not None else llm_output


    def prepare_query_and_schema(self, query, debug):
        is_query_valid = is_valid_json(query)
        if not is_query_valid:
            raise ValueError("Invalid query. Please provide a valid JSON query.")

        query_keys = get_json_keys_as_string(query)
        query_schema = query
        query = "retrieve " + query_keys

        query = query + ". return response in JSON format, by strictly following this JSON schema: " + query_schema

        return query, query_schema


    def execute_query(self, options, query_all_data, query, file_path, debug):
        extractor = VLLMExtractor()

        # export HF_TOKEN="hf_"
        config = {}
        if options[0] == 'huggingface':
            config = {
                "method": options[0],  # Could be 'huggingface' or 'local_gpu'
                "hf_space": options[1],
                "hf_token": os.getenv('HF_TOKEN')
            }
        else:
            # Handle other cases if needed
            return "First element is not 'huggingface'"

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
        llm_output = extractor.run_inference(model_inference_instance, input_data, generic_query=query_all_data,
                                             debug=debug)

        return llm_output


    def validate_result(self, llm_output, query_all_data, query_schema, debug):
        validator = Validator(query_schema)

        validation_result = validator.validate_json_against_schema(llm_output, validator.generated_schema)
        if validation_result is not None:
            return validation_result
        else:
            if debug:
                print("LLM output is valid according to the schema.")


    def invoke_pipeline_step(self, task_call, task_description, local):
        if local:
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=False,
            ) as progress:
                progress.add_task(description=task_description, total=None)
                ret = task_call()
        else:
            print(task_description)
            ret = task_call()

        return ret