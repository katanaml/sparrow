from sparrow_parse.vlmb.inference_base import ModelInference
from vllm import LLM, SamplingParams
import os
import json
import re


class VLLMInference(ModelInference):
    """
    A class for performing inference using vLLM.
    Model loads once on initialization and stays in memory for fast inference.
    """

    def __init__(self, model_name, config=None):
        """
        Initialize the vLLM inference class with the given model name.

        :param model_name: Name of the model to load from HuggingFace.
        :param config: Optional dict with vLLM parameters (dtype, gpu_memory_utilization, etc.)
        """
        self.model_name = model_name

        # Default configuration
        default_config = {
            "dtype": "bfloat16",
            "gpu_memory_utilization": 0.9,
            "max_model_len": 32768,
            "limit_mm_per_prompt": {"image": 1},
        }

        if config:
            default_config.update(config)

        self.config = default_config

        print(f"[vLLM] Loading model: {model_name}")
        print(f"[vLLM] Config: {default_config}")

        # Initialize vLLM model (loads immediately)
        self.llm = LLM(model=model_name, **default_config)

        print(f"[vLLM] Model loaded successfully and ready for inference")

    def process_response(self, output_text):
        """
        Process and clean the model's raw output to format as JSON or return markdown/text as-is.
        """
        try:
            # Check if we have markdown code block markers
            if "```" in output_text:
                # Handle markdown-formatted output with JSON
                json_start = output_text.find("```json")
                if json_start != -1:
                    # Extract content between ```json and ```
                    content = output_text[json_start + 7:]
                    json_end = content.rfind("```")
                    if json_end != -1:
                        content = content[:json_end].strip()
                        formatted_json = json.loads(content)
                        return json.dumps(formatted_json, indent=2, ensure_ascii=False)
                else:
                    # It's markdown but not JSON - return as-is
                    return output_text

            # Handle raw JSON (no markdown formatting)
            # First try to find JSON array or object patterns
            for pattern in [r'\[\s*\{.*\}\s*\]', r'\{.*\}']:
                matches = re.search(pattern, output_text, re.DOTALL)
                if matches:
                    potential_json = matches.group(0)
                    try:
                        formatted_json = json.loads(potential_json)
                        return json.dumps(formatted_json, indent=2, ensure_ascii=False)
                    except:
                        pass

            # Last resort: try to parse the whole text as JSON
            formatted_json = json.loads(output_text.strip())
            return json.dumps(formatted_json, indent=2, ensure_ascii=False)

        except (json.JSONDecodeError, ValueError):
            # Not JSON - return original text (could be markdown or plain text)
            return output_text
        except Exception:
            # Any other unexpected error - still return original text
            return output_text

    def inference(self, input_data, apply_annotation=False, ocr_callback=None, mode=None):
        """
        Perform inference on input data using the vLLM model.

        :param input_data: A list of dictionaries containing image file paths and text inputs.
        :param apply_annotation: Optional flag to apply annotations to the output.
        :param ocr_callback: Optional callback function to modify input data before inference.
        :param mode: Optional mode for inference ("static" for simple JSON output).
        :return: List of processed model responses.
        """

        # Validate input_data
        if not input_data or not isinstance(input_data, list) or len(input_data) == 0:
            raise ValueError("input_data must be a non-empty list")

        # vLLM backend doesn't support annotations yet
        apply_annotation = False

        # Handle static mode
        if mode == "static":
            return [self.get_simple_json()]

        # Determine if we're doing text-only or image-based inference
        is_text_only = input_data[0].get("file_path") is None

        if is_text_only:
            # Text-only inference
            messages = input_data[0]["text_input"]
            response = self._generate_text_response(messages)
            results = [response]
        else:
            # Image-based inference
            file_paths = self._extract_file_paths(input_data)
            results = self._process_images(file_paths, input_data, apply_annotation, ocr_callback)

        return results

    def _generate_text_response(self, messages):
        """
        Generate a text response for text-only inputs.

        :param messages: Input messages
        :return: Generated response
        """
        try:
            # vLLM chat format for text-only
            chat_messages = [
                {
                    'role': 'user',
                    'content': messages
                }
            ]

            sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=4000
            )

            outputs = self.llm.chat(chat_messages, sampling_params=sampling_params)
            response = outputs[0].outputs[0].text

            print("Inference completed successfully")
            return self.process_response(response)
        except Exception as e:
            print(f"Error during text inference: {e}")
            raise

    def _process_images(self, file_paths, input_data, apply_annotation, ocr_callback):
        """
        Process images and generate responses for each.
        """
        results = []
        for file_path in file_paths:
            try:
                # Check if file exists
                if not os.path.exists(file_path):
                    print(f"Warning: File does not exist: {file_path}")
                    continue

                # Ensure absolute path
                file_path = os.path.abspath(file_path)

                # Prepare messages
                prompt = self._prepare_messages(file_path, input_data, apply_annotation, ocr_callback)

                # Build vLLM chat messages with image
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"file://{file_path}"}},
                        {"type": "text", "text": prompt}
                    ]
                }]

                # Generate response
                sampling_params = SamplingParams(
                    temperature=0.0,
                    max_tokens=4000
                )

                outputs = self.llm.chat(messages, sampling_params=sampling_params)
                response = outputs[0].outputs[0].text

                # Process the raw response
                processed_response = self.process_response(response)

                results.append(processed_response)
                print(f"Inference completed successfully for: {file_path}")

            except Exception as e:
                print(f"Error processing image {file_path}: {e}")
                # Continue processing other images instead of failing completely
                continue

        return results

    def _prepare_messages(self, file_path, input_data, apply_annotation, ocr_callback):
        """
        Prepare the appropriate messages/prompt for inference.

        :param file_path: Path to the image file
        :param input_data: Original input data
        :param apply_annotation: Flag to apply annotations
        :param ocr_callback: Optional OCR callback
        :return: Prompt text
        """
        # Apply OCR callback if provided
        if ocr_callback is not None:
            input_data = ocr_callback(file_path, input_data)

        # Extract text prompt from input data
        return input_data[0]["text_input"]

    @staticmethod
    def _extract_file_paths(input_data):
        """
        Extract and resolve absolute file paths from input data.

        :param input_data: List of dictionaries containing image file paths.
        :return: List of absolute file paths.
        """
        return [
            os.path.abspath(file_path)
            for data in input_data
            for file_path in data.get("file_path", [])
        ]