from rag.agents.interface import Pipeline
from sparrow_parse.vllm.inference_factory import InferenceFactory
from sparrow_parse.extractors.vllm_extractor import VLLMExtractor
import timeit
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Any, List
from .sparrow_validator import Validator
from .sparrow_utils import is_valid_json, get_json_keys_as_string, add_validation_message, add_page_number
import warnings
import os
import json


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class SparrowParsePipeline(Pipeline):

    def __init__(self):
        pass

    def run_pipeline(self,
                     agent: str,
                     query: str,
                     file_path: str,
                     options: List[str] = None,
                     debug_dir: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {agent}\n")

        start = timeit.default_timer()

        query_all_data = False
        query_schema = None
        if query == "*":
            query_all_data = True
            query = None
        else:
            try:
                query, query_schema = self.invoke_pipeline_step(lambda: self.prepare_query_and_schema(query, debug),
                                                          "Preparing query and schema", local)
            except ValueError as e:
                raise e

        llm_output_list, num_pages = self.invoke_pipeline_step(lambda: self.execute_query(options, query_all_data,
                                                                                          query,
                                                                                          file_path,
                                                                                          debug_dir,
                                                                                          debug),
                                                               "Executing query", local)

        llm_output = self.process_llm_output(llm_output_list, num_pages, query_all_data, query_schema, debug, local)

        end = timeit.default_timer()

        print(f"Time to retrieve answer: {end - start}")

        return llm_output


    def prepare_query_and_schema(self, query, debug):
        is_query_valid = is_valid_json(query)
        if not is_query_valid:
            raise ValueError("Invalid query. Please provide a valid JSON query.")

        query_keys = get_json_keys_as_string(query)
        query_schema = query
        query = "retrieve " + query_keys

        query = query + ". return response in JSON format, by strictly following this JSON schema: " + query_schema

        return query, query_schema


    def execute_query(self, options, query_all_data, query, file_path, debug_dir, debug):
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
                "file_path": file_path,
                "text_input": query
            }
        ]

        # Now you can run inference without knowing which implementation is used
        llm_output, num_pages = extractor.run_inference(model_inference_instance,
                                                        input_data,
                                                        generic_query=query_all_data,
                                                        debug_dir=debug_dir,
                                                        debug=debug,
                                                        mode=None)

        return llm_output, num_pages

    def process_single_page(self, llm_output_list, query_all_data, query_schema, debug, local):
        """
        Processes a single page of LLM output, including validation and formatting if needed.
        """
        # Extract the single page output
        llm_output = llm_output_list[0]

        if query_all_data is False:
            validation_result = self.invoke_pipeline_step(
                lambda: self.validate_result(llm_output, query_all_data, query_schema, debug),
                "Validating result", local
            )
            # Ensure llm_output is a dictionary, not a string
            if isinstance(llm_output, str):
                llm_output = json.loads(llm_output)
            llm_output = add_validation_message(llm_output, "true" if validation_result is None else validation_result)
            return json.dumps(llm_output, indent=4)
        else:
            # Return as is if query_all_data is True
            return llm_output

    def process_multiple_pages(self, llm_output_list, query_all_data, query_schema, debug, local):
        """
        Processes multiple pages of LLM output, including validation (if needed), formatting, and pagination.
        """
        llm_output_list_combined = []
        for i, llm_output_page in enumerate(llm_output_list):
            if query_all_data is False:
                validation_result = self.invoke_pipeline_step(
                    lambda: self.validate_result(llm_output_page, query_all_data, query_schema, debug),
                    f"Validating result for page {i + 1}...", local
                )
                # Ensure llm_output_page is a dictionary, not a string
                if isinstance(llm_output_page, str):
                    llm_output_page = json.loads(llm_output_page)
                llm_output_page = add_validation_message(llm_output_page,
                                                         "true" if validation_result is None else validation_result)
            else:
                # Ensure llm_output_page is a dictionary if query_all_data is True
                if isinstance(llm_output_page, str):
                    llm_output_page = json.loads(llm_output_page)

            llm_output_page = add_page_number(llm_output_page, i + 1)
            llm_output_list_combined.append(llm_output_page)

        return json.dumps(llm_output_list_combined, indent=4)

    def process_llm_output(self, llm_output_list, num_pages, query_all_data, query_schema, debug, local):
        """
        Processes the LLM output based on the number of pages.
        """
        if num_pages == 1:
            # Pass the entire list to process_single_page for encapsulation
            return self.process_single_page(llm_output_list, query_all_data, query_schema, debug, local)
        elif num_pages > 1:
            return self.process_multiple_pages(llm_output_list, query_all_data, query_schema, debug, local)
        return None


    def validate_result(self, llm_output, query_all_data, query_schema, debug):
        validator = Validator(query_schema)

        validation_result = validator.validate_json_against_schema(llm_output, validator.generated_schema)
        if validation_result is not None:
            return validation_result
        else:
            if debug:
                print("LLM output is valid according to the schema.")
            return None


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