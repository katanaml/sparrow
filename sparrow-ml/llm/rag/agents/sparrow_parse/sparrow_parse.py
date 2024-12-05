# Standard library imports
import json
import os
import timeit
import warnings
from typing import Any, List, Tuple, Optional, Dict

# Third-party library imports
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

# Local imports
from .sparrow_validator import JSONValidator
from .sparrow_utils import (
    is_valid_json,
    get_json_keys_as_string,
    add_validation_message,
    add_page_number
)
from sparrow_parse.extractors.vllm_extractor import VLLMExtractor
from sparrow_parse.vllm.inference_factory import InferenceFactory
from rag.agents.interface import Pipeline


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

        # Handle special case where query indicates fetching all data
        query_all_data = query == "*"
        query_schema = None

        if query_all_data:
            query = None
        else:
            query, query_schema = self._prepare_query(query, local)

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


    def _prepare_query(self, query: str, local: bool) -> Tuple[str, Optional[Dict]]:
        """Prepare the query and schema, raising errors as necessary."""
        try:
            return self.invoke_pipeline_step(
                lambda: self.prepare_query_and_schema(query),
                "Preparing query and schema",
                local
            )
        except ValueError as e:
            raise ValueError(f"Error preparing query: {e}")


    def prepare_query_and_schema(self, query):
        is_query_valid = is_valid_json(query)
        if not is_query_valid:
            raise ValueError("Invalid query. Please provide a valid JSON query.")

        query_keys = get_json_keys_as_string(query)
        query_schema = query
        query = "retrieve " + query_keys

        query = query + ". return response in JSON format, by strictly following this JSON schema: " + query_schema

        return query, query_schema

    def execute_query(self, options, query_all_data, query, file_path, debug_dir, debug):
        """
        Executes the query using the specified inference backend.

        Args:
            options (list): Inference backend options (e.g., ['huggingface', 'some_space']).
            query_all_data (bool): Indicates if all data should be queried.
            query (str): Query text.
            file_path (str): Path to the file for querying.
            debug_dir (str): Directory for debug output.
            debug (bool): Flag for enabling debug mode.

        Returns:
            Tuple: (llm_output, num_pages) - The output from the inference and the number of pages processed.
        """
        # Initialize the extractor
        extractor = VLLMExtractor()

        # Validate and configure the inference backend
        config = self._configure_inference_backend(options)
        if config is None:
            return "Inference backend is not set up for this option", 1

        # Create the inference instance
        factory = InferenceFactory(config)
        model_inference_instance = factory.get_inference_instance()

        # Prepare input data for inference
        input_data = [
            {
                "file_path": file_path,
                "text_input": query
            }
        ]

        # Run inference using the selected backend
        llm_output, num_pages = extractor.run_inference(
            model_inference_instance,
            input_data,
            generic_query=query_all_data,
            debug_dir=debug_dir,
            debug=debug,
            mode=None
        )

        return llm_output, num_pages

    @staticmethod
    def _configure_inference_backend(options):
        """
        Configures the inference backend based on the provided options.

        Args:
            options (list): Inference backend options.

        Returns:
            dict: Configuration dictionary for the selected backend, or None if invalid.
        """
        if not options or len(options) < 2:
            raise ValueError("Invalid options provided for inference backend configuration.")

        method = options[0].lower()
        if method == 'huggingface':
            return {
                "method": method,
                "hf_space": options[1],
                "hf_token": os.getenv('HF_TOKEN')  # Ensure HF_TOKEN is set in the environment
            }
        elif method == 'mlx':
            return {
                "method": method,
                "model_name": options[1]
            }
        else:
            # Extendable for additional backends
            print(f"Unsupported inference method: {method}")
            return None


    def process_single_page(self, llm_output_list, query_all_data, query_schema, debug, local):
        """
        Processes a single page of LLM output, including validation and formatting if needed.
        """
        llm_output = llm_output_list[0]

        if not query_all_data:
            validation_result = self.invoke_pipeline_step(
                lambda: self.validate_result(llm_output, query_all_data, query_schema, debug),
                "Validating result", local
            )

            try:
                llm_output = json.loads(llm_output) if isinstance(llm_output, str) else llm_output
                llm_output = add_validation_message(llm_output,
                                                    "true" if validation_result is None else validation_result)
            except json.JSONDecodeError:
                llm_output = {
                    "message": "Invalid JSON format in LLM output",
                    "valid": validation_result
                }
            return json.dumps(llm_output, indent=4)

        return llm_output


    def process_multiple_pages(self, llm_output_list, query_all_data, query_schema, debug, local):
        """
        Processes multiple pages of LLM output, including validation (if needed), formatting, and pagination.
        """
        combined_output = []

        for i, llm_output in enumerate(llm_output_list):
            if not query_all_data:
                validation_result = self.invoke_pipeline_step(
                    lambda: self.validate_result(llm_output, query_all_data, query_schema, debug),
                    f"Validating result for page {i + 1}...", local
                )

                try:
                    llm_output = json.loads(llm_output) if isinstance(llm_output, str) else llm_output
                    llm_output = add_validation_message(llm_output,
                                                        "true" if validation_result is None else validation_result)
                except json.JSONDecodeError:
                    llm_output = {
                        "message": "Invalid JSON format in LLM output",
                        "valid": validation_result
                    }
            else:
                try:
                    llm_output = json.loads(llm_output) if isinstance(llm_output, str) else llm_output
                except json.JSONDecodeError:
                    llm_output = {
                        "message": "Invalid JSON format in LLM output",
                        "valid": "false"
                    }

            llm_output = add_page_number(llm_output, i + 1)
            combined_output.append(llm_output)

        return json.dumps(combined_output, indent=4)


    def process_llm_output(self, llm_output_list, num_pages, query_all_data, query_schema, debug, local):
        """
        Processes the LLM output based on the number of pages.
        """
        if num_pages == 1:
            return self.process_single_page(llm_output_list, query_all_data, query_schema, debug, local)
        if num_pages > 1:
            return self.process_multiple_pages(llm_output_list, query_all_data, query_schema, debug, local)
        return None


    @staticmethod
    def validate_result(llm_output, query_all_data, query_schema, debug):
        """
        Validates the LLM output against the provided schema.

        Args:
            llm_output (dict or str): The output to validate.
            query_all_data (bool): Whether to bypass validation.
            query_schema (dict): The schema to validate against.
            debug (bool): Whether to print debug information.

        Returns:
            str or None: Validation result if invalid; otherwise, None.
        """
        validator = JSONValidator(query_schema)
        validation_result = validator.validate_json_against_schema(llm_output, validator.generated_schema)

        if debug:
            if validation_result is not None:
                print("Validation failed:")
                print("- Errors:", validation_result)
                print("- Output:", llm_output)
            else:
                print("Validation passed. LLM output conforms to the schema.")

        return validation_result


    @staticmethod
    def invoke_pipeline_step(task_call, task_description, local):
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