import json

from sparrow_parse.vllm.inference_factory import InferenceFactory
from sparrow_parse.helpers.pdf_optimizer import PDFOptimizer
from sparrow_parse.processors.table_structure_processor import TableDetector
from rich import print
import os
import tempfile
import shutil
from typing import Any, Dict, List, Union


class VLLMExtractor(object):
    def __init__(self):
        pass

    def run_inference(self, model_inference_instance, input_data, tables_only=False,
                      generic_query=False, debug_dir=None, debug=False, mode=None):
        """
        Main entry point for processing input data using a model inference instance.
        Handles generic queries, PDFs, and table extraction.
        """
        if generic_query:
            input_data[0]["text_input"] = "retrieve document data. return response in JSON format"

        if debug:
            print("Input data:", input_data)

        file_path = input_data[0]["file_path"]
        if self.is_pdf(file_path):
            return self._process_pdf(model_inference_instance, input_data, tables_only, debug, debug_dir, mode)

        return self._process_non_pdf(model_inference_instance, input_data, tables_only, debug, debug_dir)


    def _process_pdf(self, model_inference_instance, input_data, tables_only, debug, debug_dir, mode):
        """
        Handles processing and inference for PDF files, including page splitting and optional table extraction.
        """
        pdf_optimizer = PDFOptimizer()
        num_pages, output_files, temp_dir = pdf_optimizer.split_pdf_to_pages(input_data[0]["file_path"],
                                                                             debug_dir, convert_to_images=True)

        results = self._process_pages(model_inference_instance, output_files, input_data, tables_only, debug, debug_dir)

        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        return results, num_pages


    def _process_non_pdf(self, model_inference_instance, input_data, tables_only, debug, debug_dir):
        """
        Handles processing and inference for non-PDF files, with optional table extraction.
        """
        file_path = input_data[0]["file_path"]
        if tables_only:
            return [self._extract_tables(model_inference_instance, file_path, input_data, debug, debug_dir)], 1
        else:
            input_data[0]["file_path"] = [file_path]
            results = model_inference_instance.inference(input_data)
            return results, 1

    def _process_pages(self, model_inference_instance, output_files, input_data, tables_only, debug, debug_dir):
        """
        Processes individual pages (PDF split) and handles table extraction or inference.

        Args:
            model_inference_instance: The model inference object.
            output_files: List of file paths for the split PDF pages.
            input_data: Input data for inference.
            tables_only: Whether to only process tables.
            debug: Debug flag for logging.
            debug_dir: Directory for saving debug information.

        Returns:
            List of results from the processing or inference.
        """
        results_array = []

        if tables_only:
            if debug:
                print(f"Processing {len(output_files)} pages for table extraction.")
            # Process each page individually for table extraction
            for i, file_path in enumerate(output_files):
                tables_result = self._extract_tables(
                    model_inference_instance, file_path, input_data, debug, debug_dir, page_index=i
                )
                results_array.append(tables_result)
        else:
            if debug:
                print(f"Processing {len(output_files)} pages for inference at once.")
            # Pass all output files to the inference method for processing at once
            input_data[0]["file_path"] = output_files
            results = model_inference_instance.inference(input_data)
            results_array.extend(results)

        return results_array


    def _extract_tables(self, model_inference_instance, file_path, input_data, debug, debug_dir, page_index=None):
        """
        Detects and processes tables from an input file.
        """
        table_detector = TableDetector()
        cropped_tables = table_detector.detect_tables(file_path, local=False, debug_dir=debug_dir, debug=debug)
        results_array = []
        temp_dir = tempfile.mkdtemp()

        for i, table in enumerate(cropped_tables):
            table_index = f"page_{page_index + 1}_table_{i + 1}" if page_index is not None else f"table_{i + 1}"
            print(f"Processing {table_index} for document {file_path}")

            output_filename = os.path.join(temp_dir, f"{table_index}.jpg")
            table.save(output_filename, "JPEG")

            input_data[0]["file_path"] = [output_filename]
            result = self._run_model_inference(model_inference_instance, input_data)
            result = self.add_table_info_to_data(result, "table_nr", i + 1)
            results_array.append(result)

        shutil.rmtree(temp_dir, ignore_errors=True)
        return json.dumps(results_array, indent=4)


    @staticmethod
    def _run_model_inference(model_inference_instance, input_data):
        """
        Runs model inference and handles JSON decoding.
        """
        result = model_inference_instance.inference(input_data)[0]
        try:
            return json.loads(result) if isinstance(result, str) else result
        except json.JSONDecodeError:
            return {"message": "Invalid JSON format in LLM output", "valid": "false"}


    @staticmethod
    def is_pdf(file_path):
        """Checks if a file is a PDF based on its extension."""
        return file_path.lower().endswith('.pdf')


    @staticmethod
    def add_table_info_to_data(data: Union[Dict, List], key: str, message: Any) -> Dict:
        """
        Add a key-value pair to a dictionary or wrap a list in a dictionary.
        If a 'table' key exists, add or update the key-value pair inside it.

        Args:
            data (Union[Dict, List]): The input data (either a dictionary or list).
            key (str): The key to add.
            message (Any): The value to associate with the key.

        Returns:
            Dict: The modified data.
        """
        if isinstance(data, dict):
            if "table" in data and isinstance(data["table"], list):
                # Add or update the key-value pair in the existing structure
                data[key] = message
            else:
                # Wrap the dictionary inside a `table` key and include the additional key-value pair
                data = {"table": [data], key: message}
        elif isinstance(data, list):
            # Wrap the list in a dictionary with the additional key-value pair
            data = {"table": data, key: message}
        else:
            raise TypeError("Data must be a dictionary or a list.")
        return data


if __name__ == "__main__":
    # run locally: python -m sparrow_parse.extractors.vllm_extractor

    extractor = VLLMExtractor()

    # # export HF_TOKEN="hf_"
    # config = {
    #     "method": "mlx",  # Could be 'huggingface', 'mlx' or 'local_gpu'
    #     "model_name": "mlx-community/Qwen2-VL-72B-Instruct-4bit",
    #     # "hf_space": "katanaml/sparrow-qwen2-vl-7b",
    #     # "hf_token": os.getenv('HF_TOKEN'),
    #     # Additional fields for local GPU inference
    #     # "device": "cuda", "model_path": "model.pth"
    # }
    #
    # # Use the factory to get the correct instance
    # factory = InferenceFactory(config)
    # model_inference_instance = factory.get_inference_instance()
    #
    # input_data = [
    #     {
    #         "file_path": "/Users/andrejb/Work/katana-git/sparrow/sparrow-ml/llm/data/invoice_1.jpg",
    #         "text_input": "retrieve document data. return response in JSON format"
    #     }
    # ]
    #
    # # Now you can run inference without knowing which implementation is used
    # results_array, num_pages = extractor.run_inference(model_inference_instance, input_data, tables_only=False,
    #                                                    generic_query=False,
    #                                                    debug_dir="/Users/andrejb/Work/katana-git/sparrow/sparrow-ml/llm/data/",
    #                                                    debug=True,
    #                                                    mode=None)
    #
    # for i, result in enumerate(results_array):
    #     print(f"Result for page {i + 1}:", result)
    # print(f"Number of pages: {num_pages}")