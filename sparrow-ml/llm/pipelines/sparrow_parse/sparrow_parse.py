# Standard library imports
import json
import os
import timeit
import warnings
from typing import Any, List, Tuple, Optional, Dict
from datetime import datetime

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
from .sparrow_experimental import process_ocr_data
import concurrent.futures
from pipelines.interface import Pipeline


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def subprocess_inference(config, input_data, tables_only, crop_size, query_all_data, apply_annotation, ocr_callback, debug_dir, debug):
    """
    Subprocess function to execute the inference logic.
    """
    from sparrow_parse.extractors.vllm_extractor import VLLMExtractor
    from sparrow_parse.vllm.inference_factory import InferenceFactory

    # Initialize the extractor and inference instance
    factory = InferenceFactory(config)
    model_inference_instance = factory.get_inference_instance()
    extractor = VLLMExtractor()

    # Run inference
    llm_output, num_pages = extractor.run_inference(
        model_inference_instance,
        input_data,
        tables_only=tables_only,
        generic_query=query_all_data,
        crop_size=crop_size,
        debug_dir=debug_dir,
        apply_annotation=apply_annotation,
        ocr_callback=ocr_callback,
        debug=debug,
        mode=None
    )

    # Return results
    return llm_output, num_pages


class SparrowParsePipeline(Pipeline):

    def __init__(self):
        pass

    def run_pipeline(self,
                     pipeline: str,
                     query: str,
                     file_path: str,
                     options: List[str] = None,
                     crop_size: int = None,
                     instruction: bool = False,
                     validation: bool = False,
                     ocr: bool = False,
                     markdown: bool = False,
                     page_type: List[str] = None,
                     debug_dir: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {pipeline}\n")

        start = timeit.default_timer()

        # Determine query processing strategy and prepare query
        query, query_schema, query_all_data = self._process_query(query, instruction, validation, markdown, page_type, local)

        # Check if ocr is enabled and set callback accordingly
        ocr_callback = process_ocr_data if ocr else None

        llm_output_list, num_pages, tables_only, validation_off, apply_annotation = self.invoke_pipeline_step(
            lambda: self.execute_query(options, crop_size, query_all_data, ocr_callback, query, file_path, debug_dir, debug),
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executing query", 
            local
        )

        if page_type is not None:
            # if page_type is not None, we only want to get info about page type, without validating data
            validation_off = True
        if apply_annotation:
            validation_off = True
        if instruction:
            validation_off = True
        if validation:
            validation_off = True
        if markdown:
            validation_off = True

        llm_output = self.process_llm_output(llm_output_list, num_pages, query_all_data, query_schema, tables_only,
                                             validation_off, debug, local)

        end = timeit.default_timer()

        print(f"Time to retrieve answer: {end - start}")

        return llm_output


    def _process_query(self, query: str, instruction: bool, validation: bool, markdown: bool, page_type: List[str], local: bool) -> Tuple[
        str, Optional[Dict], bool]:
        """
        Process and prepare the query based on the input parameters.

        Returns:
            Tuple[str, Optional[Dict], bool]: (processed_query, query_schema, query_all_data)
        """
        query_all_data = query == "*"

        if query_all_data:
            if page_type is not None:
                # Special case: query="*" with page_type means page type detection only
                return self._prepare_page_type_query(page_type, local), None, False
            else:
                # True "all data" query
                return None, None, True

        # Non-wildcard queries
        if instruction:
            return self._prepare_instruction_query(query, local), None, False
        elif validation:
            return self._prepare_validation_query(query, local), None, False
        elif markdown:
            return self._prepare_markdown_query(query, local), None, False
        else:
            processed_query, schema = self._prepare_query(query, local)
            return processed_query, schema, False


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


    def _prepare_page_type_query(self, page_type: list[str], local: bool) -> str:
        """Prepare the query and schema, raising errors as necessary."""
        try:
            return self.invoke_pipeline_step(
                lambda: self.prepare_page_type_query(page_type),
                "Preparing page type query",
                local
            )
        except ValueError as e:
            raise ValueError(f"Error preparing page type query: {e}")
        
        
    def _prepare_instruction_query(self, query: str, local: bool) -> str:
        """Prepare the query and schema, raising errors as necessary."""
        try:
            return self.invoke_pipeline_step(
                lambda: self.prepare_instruction_query(query),
                "Preparing instruction query",
                local
            )
        except ValueError as e:
            raise ValueError(f"Error preparing instruction query: {e}")


    def _prepare_validation_query(self, query: str, local: bool) -> str:
        """Prepare the query and schema, raising errors as necessary."""
        try:
            return self.invoke_pipeline_step(
                lambda: self.prepare_validation_query(query),
                "Preparing validation query",
                local
            )
        except ValueError as e:
            raise ValueError(f"Error preparing validation query: {e}")


    def _prepare_markdown_query(self, query: str, local: bool) -> str:
        """Prepare the query and schema, raising errors as necessary."""
        try:
            return self.invoke_pipeline_step(
                lambda: self.prepare_markdown_query(query),
                "Preparing markdown query",
                local
            )
        except ValueError as e:
            raise ValueError(f"Error preparing markdown query: {e}")


    @staticmethod
    def prepare_query_and_schema(query):
        is_query_valid = is_valid_json(query)
        if not is_query_valid:
            raise ValueError("Invalid query. Please provide a valid JSON query.")

        query_keys = get_json_keys_as_string(query)
        query_schema = query
        query = "retrieve data based on provided JSON schema"

        query = (query + ". return response in JSON format, by strictly following this JSON schema: " + query_schema +
                 ". If a field is not visible or cannot be found in the document, return null. Do not guess, infer, or generate values for missing fields.")

        return query, query_schema


    @staticmethod
    def prepare_page_type_query(page_type):
        if not page_type:  # Handle empty array
            return ""

        # Convert all elements to strings and join with comma
        page_types =  ", ".join(str(item) for item in page_type)

        query  = f"detect page type based on this list of types - {page_types}. return response in JSON format"

        return query


    @staticmethod
    def prepare_instruction_query(query):
        query = f"{query}. response must be short, with values to answer the question, no need to provide other values. return response in JSON format"

        return query


    @staticmethod
    def prepare_validation_query(query):
        query = f"validate if listed fields - {query} are present in the document. format response with field name and boolean value. return response in JSON format"

        return query

    @staticmethod
    def prepare_markdown_query(query):
        query = f"\n<|grounding|>Convert the document to markdown."

        return query


    def execute_query(self, options, crop_size, query_all_data, ocr_callback, query, file_path, debug_dir, debug):
        """
        Executes the query using the specified inference backend in a subprocess.

        Args:
            options (list): Inference backend options (e.g., ['huggingface', 'some_space']).
            crop_size (int): Crop size for table extraction.
            query_all_data (bool): Indicates if all data should be queried.
            ocr_callback (callable): Callback function for ocr processing.
            query (str): Query text.
            file_path (str): Path to the file for querying.
            debug_dir (str): Directory for debug output.
            debug (bool): Flag for enabling debug mode.

        Returns:
            Tuple: (llm_output, num_pages, tables_only, validation_off, apply_annotation)
        """
        # Validate and configure the inference backend
        config, tables_only, validation_off, apply_annotation = self._configure_inference_backend(options)
        if config is None:
            return "Inference backend is not set up for this option", 1, tables_only, validation_off

        # Prepare input data for inference
        input_data = [
            {
                "file_path": file_path,
                "text_input": query
            }
        ]

        # Offload inference to a subprocess
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future = executor.submit(
                subprocess_inference,  # Call the top-level function
                config,
                input_data,
                tables_only,
                crop_size,
                query_all_data,
                apply_annotation,
                ocr_callback,
                debug_dir,
                debug
            )
            llm_output, num_pages = future.result()

        return llm_output, num_pages, tables_only, validation_off, apply_annotation


    @staticmethod
    def _configure_inference_backend(options):
        """
        Configures the inference backend based on the provided options.

        Args:
            options (list): Inference backend options.

        Returns:
            tuple:
                - dict: Configuration dictionary for the selected backend, or None if invalid.
                - bool: True if "tables_only" is specified in the options, False otherwise.
                - bool: True if "validation_off" is specified in the options, False otherwise.
                - bool: True if "apply_annotation" is specified in the options, False otherwise.
        """
        if not options or len(options) < 2:
            raise ValueError("Invalid options provided for inference backend configuration.")

        method = options[0].lower()
        tables_only = "tables_only" in [opt.lower() for opt in options[2:]]
        validation_off = "validation_off" in [opt.lower() for opt in options[2:]]
        apply_annotation = "apply_annotation" in [opt.lower() for opt in options[2:]]

        if method == 'huggingface':
            return {
                "method": method,
                "hf_space": options[1],
                "hf_token": os.getenv('HF_TOKEN')  # Ensure HF_TOKEN is set in the environment
            }, tables_only, validation_off, apply_annotation
        elif method == 'mlx':
            return {
                "method": method,
                "model_name": options[1]
            }, tables_only, validation_off, apply_annotation
        elif method == 'ollama':
            return {
                "method": method,
                "model_name": options[1]
            }, tables_only, validation_off, apply_annotation
        else:
            # Extendable for additional backends
            print(f"Unsupported inference method: {method}")
            return None, tables_only, validation_off, apply_annotation


    def process_single_page(self, llm_output_list, query_all_data, query_schema, tables_only, validation_off, debug, local):
        """
        Processes a single page of LLM output, including validation and formatting if needed.
        """
        llm_output = llm_output_list[0]

        if not query_all_data and not tables_only and not validation_off:
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
            return json.dumps(llm_output, indent=4, ensure_ascii=False)

        return llm_output


    def process_multiple_pages(self, llm_output_list, query_all_data, query_schema, tables_only, validation_off, debug, local):
        """
        Processes multiple pages of LLM output, including validation (if needed), formatting, and pagination.
        """
        combined_output = []

        for i, llm_output in enumerate(llm_output_list):
            if not query_all_data and not tables_only and not validation_off:
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

        return json.dumps(combined_output, indent=4, ensure_ascii=False)


    def process_llm_output(self, llm_output_list, num_pages, query_all_data, query_schema, tables_only, validation_off,
                           debug, local):
        """
        Processes the LLM output based on the number of pages.
        """
        if num_pages == 1:
            return self.process_single_page(llm_output_list, query_all_data, query_schema, tables_only, validation_off,
                                            debug, local)
        if num_pages > 1:
            return self.process_multiple_pages(llm_output_list, query_all_data, query_schema, tables_only,
                                               validation_off, debug, local)
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
                progress_task = progress.add_task(description=task_description, total=None)
                ret = task_call()
                progress.update(progress_task, completed=1)
        else:
            print(task_description)
            ret = task_call()

        return ret