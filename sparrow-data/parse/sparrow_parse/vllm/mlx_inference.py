from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_image
from sparrow_parse.vllm.inference_base import ModelInference
import os
import json, re
from rich import print


class MLXInference(ModelInference):
    """
        A class for performing inference using the MLX model.
        Handles image preprocessing, response formatting, and model interaction.
        """

    def __init__(self, model_name):
        """
        Initialize the inference class with the given model name.

        :param model_name: Name of the model to load.
        """
        self.model_name = model_name
        print(f"MLXInference initialized for model: {model_name}")


    @staticmethod
    def _load_model_and_processor(model_name):
        """
        Load the model and processor for inference.

        :param model_name: Name of the model to load.
        :return: Tuple containing the loaded model and processor.
        """
        model, processor = load(model_name)
        print(f"Loaded model: {model_name}")
        return model, processor


    def process_response(self, output_text):
        """
        Process and clean the model's raw output to format as JSON.
        """
        try:
            # Check if we have markdown code block markers
            if "```" in output_text:
                # Handle markdown-formatted output
                json_start = output_text.find("```json")
                if json_start != -1:
                    # Extract content between ```json and ```
                    content = output_text[json_start + 7:]
                    json_end = content.rfind("```")
                    if json_end != -1:
                        content = content[:json_end].strip()
                        formatted_json = json.loads(content)
                        return json.dumps(formatted_json, indent=2)

            # Handle raw JSON (no markdown formatting)
            # First try to find JSON array or object patterns
            for pattern in [r'\[\s*\{.*\}\s*\]', r'\{.*\}']:
                import re
                matches = re.search(pattern, output_text, re.DOTALL)
                if matches:
                    potential_json = matches.group(0)
                    try:
                        formatted_json = json.loads(potential_json)
                        return json.dumps(formatted_json, indent=2)
                    except:
                        pass

            # Last resort: try to parse the whole text as JSON
            formatted_json = json.loads(output_text.strip())
            return json.dumps(formatted_json, indent=2)

        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            return output_text


    def load_image_data(self, image_filepath, max_width=1250, max_height=1750):
        """
        Load and resize image while maintaining its aspect ratio.
        Returns both original and resized dimensions for coordinate mapping.
        """
        image = load_image(image_filepath)
        orig_width, orig_height = image.size

        # Calculate new dimensions while maintaining the aspect ratio
        if orig_width > max_width or orig_height > max_height:
            aspect_ratio = orig_width / orig_height
            new_width = min(max_width, int(max_height * aspect_ratio))
            new_height = min(max_height, int(max_width / aspect_ratio))
            return image, new_width, new_height, orig_width, orig_height

        # No resize needed, original dimensions are used
        return image, orig_width, orig_height, orig_width, orig_height


    def scale_bbox_coordinates(self, json_response, orig_width, orig_height, resized_width, resized_height):
        """
        Scale bbox coordinates from resized image dimensions back to original image dimensions.
        Only used when apply_annotation=True.
        """
        # Calculate scale factors
        scale_x = orig_width / resized_width
        scale_y = orig_height / resized_height

        # No scaling needed if dimensions are the same
        if scale_x == 1 and scale_y == 1:
            return json_response

        # Helper function to recursively process JSON objects
        def process_object(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "bbox" and isinstance(value, list) and len(value) == 4:
                        # Scale the bbox coordinates
                        obj[key] = [
                            value[0] * scale_x,  # x_min
                            value[1] * scale_y,  # y_min
                            value[2] * scale_x,  # x_max
                            value[3] * scale_y  # y_max
                        ]
                    elif isinstance(value, (dict, list)):
                        process_object(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, (dict, list)):
                        process_object(item)
            return obj

        return process_object(json_response)


    def inference(self, input_data, apply_annotation=False, mode=None):
        """
        Perform inference on input data using the specified model.

        :param input_data: A list of dictionaries containing image file paths and text inputs.
        :param apply_annotation: Optional flag to apply annotations to the output.
        :param mode: Optional mode for inference ("static" for simple JSON output).
        :return: List of processed model responses.
        """
        # Handle static mode
        if mode == "static":
            return [self.get_simple_json()]

        # Load the model and processor
        model, processor = self._load_model_and_processor(self.model_name)
        config = model.config
        
        # Determine if we're doing text-only or image-based inference
        is_text_only = input_data[0].get("file_path") is None
        
        if is_text_only:
            # Text-only inference
            messages = input_data[0]["text_input"]
            response = self._generate_text_response(model, processor, config, messages)
            results = [response]
        else:
            # Image-based inference
            file_paths = self._extract_file_paths(input_data)
            results = self._process_images(model, processor, config, file_paths, input_data, apply_annotation)
        
        return results

    def _generate_text_response(self, model, processor, config, messages):
        """
        Generate a text response for text-only inputs.
        
        :param model: The loaded model
        :param processor: The loaded processor
        :param config: Model configuration
        :param messages: Input messages
        :return: Generated response
        """
        prompt = apply_chat_template(processor, config, messages)
        response =  generate(
            model,
            processor,
            prompt,
            max_tokens=4000,
            temperature=0.0,
            verbose=False
        )
        print("Inference completed successfully")
        return response


    def _process_images(self, model, processor, config, file_paths, input_data, apply_annotation):
        """
        Process images and generate responses for each.
        Always resize images for memory efficiency, but scale coordinates back for annotation cases.
        """
        results = []
        for file_path in file_paths:
            # Always get both original and resized dimensions
            image, resized_width, resized_height, orig_width, orig_height = self.load_image_data(file_path)

            # Prepare messages based on model type
            messages = self._prepare_messages(input_data, apply_annotation)

            # Always use resize_shape for memory efficiency
            prompt = apply_chat_template(processor, config, messages)
            response, _ = generate(
                model,
                processor,
                prompt,
                image,
                resize_shape=(resized_width, resized_height),
                max_tokens=4000,
                temperature=0.0,
                verbose=False
            )

            # Process the raw response
            processed_response = self.process_response(response)

            # Scale coordinates if apply_annotation is True and resizing was applied
            if apply_annotation:
                try:
                    # Parse the JSON response
                    json_response = json.loads(processed_response) if isinstance(processed_response,
                                                                                 str) else processed_response

                    # Apply scaling only if dimensions differ
                    if orig_width != resized_width or orig_height != resized_height:
                        json_response = self.scale_bbox_coordinates(
                            json_response,
                            orig_width,
                            orig_height,
                            resized_width,
                            resized_height
                        )

                    # Convert back to JSON string
                    processed_response = json.dumps(json_response, indent=2)
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Warning: Could not scale coordinates - {e}")
                    # Keep the original response if JSON parsing fails

            results.append(processed_response)
            print(f"Inference completed successfully for: {file_path}")

        return results


    def transform_query_with_bbox(self, text_input):
        """
        Transform JSON schema in text_input to include value, bbox, and confidence.
        Works with formats like: "retrieve field1, field2. return response in JSON format,
        by strictly following this JSON schema: [{...}]."

        Args:
            text_input (str): The input text containing a JSON schema

        Returns:
            str: Text with transformed JSON including value, bbox, and confidence
        """

        schema_pattern = r'JSON schema:\s*(\[.*?\]|\{.*?\})'
        schema_match = re.search(schema_pattern, text_input, re.DOTALL)

        if not schema_match:
            return text_input  # Return original if pattern not found

        # Extract the schema part and its position
        schema_str = schema_match.group(1).strip()
        schema_start = schema_match.start(1)
        schema_end = schema_match.end(1)

        # Parse and transform the JSON
        try:
            # Handle single quotes if needed
            schema_str = schema_str.replace("'", '"')

            json_obj = json.loads(schema_str)
            transformed_json = self.transform_query_structure(json_obj)
            transformed_json_str = json.dumps(transformed_json)

            # Rebuild the text by replacing just the schema portion
            result = text_input[:schema_start] + transformed_json_str + text_input[schema_end:]

            return result
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON schema: {e}")
            return text_input  # Return original if parsing fails


    def transform_query_structure(self, json_obj):
        """
        Transform each field in the JSON structure to include value, bbox, and confidence.
        Handles both array and object formats recursively.
        """
        if isinstance(json_obj, list):
            # Handle array format
            return [self.transform_query_structure(item) for item in json_obj]
        elif isinstance(json_obj, dict):
            # Handle object format
            result = {}
            for key, value in json_obj.items():
                if isinstance(value, (dict, list)):
                    # Recursively transform nested objects or arrays
                    result[key] = self.transform_query_structure(value)
                else:
                    # Transform simple value to object with value, bbox, and confidence
                    result[key] = {
                        "value": value,
                        "bbox": ["float", "float", "float", "float"],
                        "confidence": "float"
                    }
            return result
        else:
            # For primitive values, no transformation needed
            return json_obj


    def _prepare_messages(self, input_data, apply_annotation):
        """
        Prepare the appropriate messages based on the model type.
        
        :param input_data: Original input data
        :param apply_annotation: Flag to apply annotations
        :return: Properly formatted messages
        """
        if "mistral" in self.model_name.lower():
            return input_data[0]["text_input"]
        elif "qwen" in self.model_name.lower():
            if apply_annotation:
                system_prompt = {"role": "system", "content": "You are an expert at extracting text from images. "
                                                              "For each item in the table, provide separate bounding boxes for each field. "
                                                              "All coordinates should be in pixels relative to the original image. Format your response in JSON."}
                user_prompt = {"role": "user", "content": self.transform_query_with_bbox(input_data[0]["text_input"])}
                return [system_prompt, user_prompt]
            return [
                {"role": "system", "content": "You are an expert at extracting structured text from image documents."},
                {"role": "user", "content": input_data[0]["text_input"]},
            ]
        else:
            raise ValueError("Unsupported model type. Please use either Mistral or Qwen.")

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