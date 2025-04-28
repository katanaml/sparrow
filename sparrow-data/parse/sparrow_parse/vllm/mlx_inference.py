from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_image
from sparrow_parse.vllm.inference_base import ModelInference
import os
import json
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

        :param image_filepath: Path to the image file.
        :param max_width: Maximum allowed width of the image.
        :param max_height: Maximum allowed height of the image.
        :return: Tuple containing the image object and its new dimensions.
        """
        image = load_image(image_filepath)  # Assuming load_image is defined elsewhere
        width, height = image.size

        # Calculate new dimensions while maintaining the aspect ratio
        if width > max_width or height > max_height:
            aspect_ratio = width / height
            new_width = min(max_width, int(max_height * aspect_ratio))
            new_height = min(max_height, int(max_width / aspect_ratio))
            return image, new_width, new_height

        return image, width, height


    def inference(self, input_data, mode=None):
        """
        Perform inference on input data using the specified model.

        :param input_data: A list of dictionaries containing image file paths and text inputs.
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
            results = self._process_images(model, processor, config, file_paths, input_data)
        
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

    def _process_images(self, model, processor, config, file_paths, input_data):
        """
        Process images and generate responses for each.
        
        :param model: The loaded model
        :param processor: The loaded processor
        :param config: Model configuration
        :param file_paths: List of image file paths
        :param input_data: Original input data
        :return: List of processed responses
        """
        results = []
        for file_path in file_paths:
            image, width, height = self.load_image_data(file_path)
            
            # Prepare messages based on model type
            messages = self._prepare_messages(input_data, file_path)
            
            # Generate and process response
            prompt = apply_chat_template(processor, config, messages)
            response = generate(
                model,
                processor,
                prompt,
                image,
                resize_shape=(width, height),
                max_tokens=4000,
                temperature=0.0,
                verbose=False
            )
            results.append(self.process_response(response))
            print(f"Inference completed successfully for: {file_path}")
        
        return results

    def _prepare_messages(self, input_data, file_path):
        """
        Prepare the appropriate messages based on the model type.
        
        :param input_data: Original input data
        :param file_path: Current file path being processed
        :return: Properly formatted messages
        """
        if "mistral" in self.model_name.lower():
            return input_data[0]["text_input"]
        else:
            return [
                {"role": "system", "content": "You are an expert at extracting structured text from image documents."},
                {"role": "user", "content": input_data[0]["text_input"]},
            ]

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