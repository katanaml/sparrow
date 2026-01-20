import json
from sparrow_parse.vllm.inference_factory import InferenceFactory
from sparrow_parse.helpers.pdf_optimizer import PDFOptimizer
from sparrow_parse.helpers.image_optimizer import ImageOptimizer
from sparrow_parse.processors.table_structure_processor import TableDetector
from rich import print
import os
import tempfile
import shutil


class VLLMExtractor(object):
    def __init__(self):
        pass

    def run_inference(self, model_inference_instance, input_data, tables_only=False,
                      generic_query=False, crop_size=None, apply_annotation=False, ocr_callback=None,
                      debug_dir=None, debug=False, mode=None):
        """
        Main entry point for processing input data using a model inference instance.
        Handles generic queries, PDFs, and table extraction.
        """
        if generic_query:
            input_data[0]["text_input"] = "retrieve document data. return response in JSON format"
            apply_annotation=False

        if debug:
            print("Input data:", input_data)

        # Handle both missing file_path and file_path=None as text-only inference
        is_text_only = "file_path" not in input_data[0] or input_data[0]["file_path"] is None

        if is_text_only:
            # Ensure file_path exists and is None for consistency
            input_data[0]["file_path"] = None
            results = model_inference_instance.inference(input_data)
            return results, 0

        # Document data extraction inference (file_path exists and is not None)
        file_path = input_data[0]["file_path"]
        if self.is_pdf(file_path):
            return self._process_pdf(model_inference_instance, input_data, tables_only, crop_size, apply_annotation, ocr_callback, debug, debug_dir, mode)
        else:
            return self._process_non_pdf(model_inference_instance, input_data, tables_only, crop_size, apply_annotation, ocr_callback, debug, debug_dir)


    def _process_pdf(self, model_inference_instance, input_data, tables_only, crop_size, apply_annotation, ocr_callback, debug, debug_dir, mode):
        """
        Handles processing and inference for PDF files, including page splitting and optional table extraction.
        """
        pdf_optimizer = PDFOptimizer()
        num_pages, output_files, temp_dir = pdf_optimizer.split_pdf_to_pages(input_data[0]["file_path"],
                                                                             debug_dir, convert_to_images=True)

        results = self._process_pages(model_inference_instance, output_files, input_data, tables_only, crop_size, apply_annotation, ocr_callback, debug, debug_dir)

        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        return results, num_pages


    def _process_non_pdf(self, model_inference_instance, input_data, tables_only, crop_size, apply_annotation, ocr_callback, debug, debug_dir):
        """
        Handles processing and inference for non-PDF files, with optional table extraction.
        """
        file_path = input_data[0]["file_path"]

        if tables_only:
            return self._extract_tables(model_inference_instance, file_path, input_data, apply_annotation, ocr_callback, debug, debug_dir), 1
        else:
            temp_dir = tempfile.mkdtemp()

            if crop_size:
                if debug:
                    print(f"Cropping image borders by {crop_size} pixels.")
                image_optimizer = ImageOptimizer()
                cropped_file_path = image_optimizer.crop_image_borders(file_path, temp_dir, debug_dir, crop_size)
                input_data[0]["file_path"] = cropped_file_path

            file_path = input_data[0]["file_path"]
            input_data[0]["file_path"] = [file_path]
            results = model_inference_instance.inference(input_data, apply_annotation, ocr_callback)

            shutil.rmtree(temp_dir, ignore_errors=True)

            return results, 1

    def _process_pages(self, model_inference_instance, output_files, input_data, tables_only, crop_size, apply_annotation, ocr_callback, debug, debug_dir):
        """
        Processes individual pages (PDF split) and handles table extraction or inference.

        Args:
            model_inference_instance: The model inference object.
            output_files: List of file paths for the split PDF pages.
            input_data: Input data for inference.
            tables_only: Whether to only process tables.
            crop_size: Size for cropping image borders.
            apply_annotation: Flag to apply annotations to the output.
            ocr_callback: Optional callback function to modify input data before inference.
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
                tables_result = self._extract_tables( model_inference_instance, file_path, input_data, apply_annotation, ocr_callback, debug, debug_dir, page_index=i)
                # Since _extract_tables returns a list with one JSON string, unpack it
                results_array.extend(tables_result)  # Unpack the single JSON string
        else:
            if debug:
                print(f"Processing {len(output_files)} pages for inference at once.")

            temp_dir = tempfile.mkdtemp()
            cropped_files = []

            if crop_size:
                if debug:
                    print(f"Cropping image borders by {crop_size} pixels from {len(output_files)} images.")

                image_optimizer = ImageOptimizer()

                # Process each file in the output_files array
                for file_path in output_files:
                    cropped_file_path = image_optimizer.crop_image_borders(
                        file_path,
                        temp_dir,
                        debug_dir,
                        crop_size
                    )
                    cropped_files.append(cropped_file_path)

                # Use the cropped files for inference
                input_data[0]["file_path"] = cropped_files
            else:
                # If no cropping needed, use original files directly
                input_data[0]["file_path"] = output_files

            # Process all files at once
            results = model_inference_instance.inference(input_data, apply_annotation, ocr_callback)
            results_array.extend(results)

            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

        return results_array


    def _extract_tables(self, model_inference_instance, file_path, input_data, apply_annotation, ocr_callback, debug, debug_dir, page_index=None):
        """
        Detects and processes tables from an input file.
        """
        table_detector = TableDetector()
        cropped_tables = table_detector.detect_tables(file_path, local=False, debug_dir=debug_dir, debug=debug)
        results_array = []

        # Check if no tables were found
        if cropped_tables is None:
            if debug:
                print(f"No tables detected in {file_path}")
            # Return a structured no-tables-found response instead of failing
            return [json.dumps({"message": "No tables detected in the document", "status": "empty"})]

        temp_dir = tempfile.mkdtemp()

        for i, table in enumerate(cropped_tables):
            table_index = f"page_{page_index + 1}_table_{i + 1}" if page_index is not None else f"table_{i + 1}"
            print(f"Processing {table_index} for document {file_path}")

            output_filename = os.path.join(temp_dir, f"{table_index}.jpg")
            table.save(output_filename, "JPEG")

            input_data[0]["file_path"] = [output_filename]
            result = self._run_model_inference(model_inference_instance, input_data, apply_annotation, ocr_callback)
            results_array.append(result)

        shutil.rmtree(temp_dir, ignore_errors=True)

        # Merge results_array elements into a single JSON structure
        merged_results = {"page_tables": results_array}

        # Format the merged results as a JSON string with indentation
        formatted_results = json.dumps(merged_results, indent=4)

        # Return the formatted JSON string wrapped in a list
        return [formatted_results]


    @staticmethod
    def _run_model_inference(model_inference_instance, input_data, apply_annotation, ocr_callback):
        """
        Runs model inference and handles JSON decoding.
        """
        result = model_inference_instance.inference(input_data, apply_annotation, ocr_callback)[0]
        try:
            return json.loads(result) if isinstance(result, str) else result
        except json.JSONDecodeError:
            return {"message": "Invalid JSON format in LLM output", "valid": "false"}


    @staticmethod
    def is_pdf(file_path):
        """Checks if a file is a PDF based on its extension."""
        return file_path.lower().endswith('.pdf')


# def ocr_callback(file_path, input_data):
#     """
#     Basic ocr callback for testing purposes.
#     Modifies input data before inference.
#
#     Args:
#         file_path: Path to the file being processed
#         input_data: Input data dictionary to be modified
#
#     Returns:
#         Modified input_data
#     """
#     print("[OCR Callback] Invoked")
#     print(f"[OCR Callback] Input data: {input_data}")
#     # Add any modifications to input_data here
#     return input_data


if __name__ == "__main__":
    # run locally: python -m sparrow_parse.extractors.vllm_extractor
    # upload:
    # python setup.py sdist bdist_wheel
    # twine upload dist/*

    extractor = VLLMExtractor()

    # # export HF_TOKEN="hf_"
    # config = {
    #     "method": "ollama",  # Could be 'huggingface', 'mlx', 'ollama' or 'local_gpu'
    #     # "model_name": "lmstudio-community/Mistral-Small-3.2-24B-Instruct-2506-MLX-8bit",
    #     # "model_name": "mlx-community/Qwen3-VL-30B-A3B-Instruct-8bit",
    #     # "model_name": "mlx-community/Qwen3-VL-8B-Instruct-bf16",
    #     "model_name": "ministral-3:14b-instruct-2512-q8_0",
    #     # "model_name": "deepseek-ocr:latest",
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
    #         "file_path": "sparrow_parse/images/bonds_table.png",
    #         "text_input": "retrieve [{\"instrument_name\":\"str\", \"valuation\":\"int\"}]. return response in JSON format"
    #     }
    # ]
    #
    # # input_data = [
    # #     {
    # #         "file_path": "sparrow_parse/images/bonds_table.png",
    # #         "text_input": "\n<|grounding|>Convert the document to markdown."
    # #     }
    # # ]
    #
    # # input_data = [
    # #     {
    # #         "file_path": None,
    # #         "text_input": "why earth is spinning around the sun?"
    # #     }
    # # ]
    #
    # # Now you can run inference without knowing which implementation is used
    # results_array, num_pages = extractor.run_inference(model_inference_instance, input_data, tables_only=False,
    #                                                    generic_query=False,
    #                                                    crop_size=0,
    #                                                    apply_annotation=False,
    #                                                    ocr_callback=ocr_callback,
    #                                                    debug_dir=None,
    #                                                    debug=True,
    #                                                    mode=None)
    #
    # for i, result in enumerate(results_array):
    #     print(f"Result for page {i + 1}:", result)
    # print(f"Number of pages: {num_pages}")

