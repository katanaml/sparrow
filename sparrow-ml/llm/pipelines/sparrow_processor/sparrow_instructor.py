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

import concurrent.futures
from pipelines.interface import Pipeline


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def subprocess_inference(config, input_data, debug_dir, debug):
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
        tables_only=False,
        generic_query=False,
        crop_size=0,
        debug_dir=debug_dir,
        debug=debug,
        mode=None
    )

    # Return results
    return llm_output, num_pages


class SparrowInstructorPipeline(Pipeline):

    def __init__(self):
        pass

    def run_pipeline(self,
                     pipeline: str,
                     query: str,
                     file_path: str,
                     options: List[str] = None,
                     crop_size: int = None,
                     page_type: List[str] = None,
                     debug_dir: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {pipeline}\n")

        start = timeit.default_timer()

        # check query to be in format "instruction: do math, payload: 2+2=", instruction: and payload: fields must be present
        if not query or "instruction:" not in query or "payload:" not in query:
            error_message = "Invalid query format. Query must contain both 'instruction:' and 'payload:' fields."
            print(error_message)
            return {"error": error_message}

        llm_output_list, num_pages = self.invoke_pipeline_step(lambda: self.execute_query(options,
                                                                                          query,
                                                                                          debug_dir,
                                                                                          debug),
                                                                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executing query", local)

        llm_output = llm_output_list[0] if len(llm_output_list) > 0 else "No output from inference backend"

        end = timeit.default_timer()

        print(f"Time to retrieve answer: {end - start}")

        return llm_output


    def execute_query(self, options, query, debug_dir, debug):
        """
        Executes the query using the specified inference backend in a subprocess.

        Args:
            options (list): Inference backend options (e.g., ['huggingface', 'some_space']).
            query (str): Query text.
            debug_dir (str): Directory for debug output.
            debug (bool): Flag for enabling debug mode.

        Returns:
            Tuple: (llm_output, num_pages)
        """
        # Validate and configure the inference backend
        config = self._configure_inference_backend(options)
        if config is None:
            return "Inference backend is not set up for this option", 0

        # Prepare input data for inference
        input_data = [
            {
                "file_path": None,
                "text_input": query
            }
        ]

        # Offload inference to a subprocess
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future = executor.submit(
                subprocess_inference,  # Call the top-level function
                config,
                input_data,
                debug_dir,
                debug
            )
            llm_output, num_pages = future.result()

        return llm_output, num_pages


    @staticmethod
    def _configure_inference_backend(options):
        """
        Configures the inference backend based on the provided options.

        Args:
            options (list): Inference backend options.

        Returns:
            tuple:
                - dict: Configuration dictionary for the selected backend, or None if invalid.
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