from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_image
from sparrow_parse.vllm.inference_base import ModelInference
import os
import json


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
        print(f"MLXInference initialized with model: {model_name}")


    @staticmethod
    def _load_model_and_processor(model_name):
        """
        Load the model and processor for inference.

        :param model_name: Name of the model to load.
        :return: Tuple containing the loaded model and processor.
        """
        return load(model_name)


    def process_response(self, output_text):
        """
        Process and clean the model's raw output to format as JSON.

        :param output_text: Raw output text from the model.
        :return: A formatted JSON string or the original text in case of errors.
        """
        try:
            cleaned_text = (
                output_text.strip("[]'")
                .replace("```json\n", "")
                .replace("\n```", "")
                .replace("'", "")
            )
            formatted_json = json.loads(cleaned_text)
            return json.dumps(formatted_json, indent=2)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON in MLX inference backend: {e}")
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
        if mode == "static":
            return [self.get_simple_json()]

        # Load the model and processor
        model, processor = self._load_model_and_processor(self.model_name)
        config = model.config

        # Prepare absolute file paths
        file_paths = self._extract_file_paths(input_data)

        results = []
        for file_path in file_paths:
            image, width, height = self.load_image_data(file_path)

            # Prepare messages for the chat model
            messages = [
                {"role": "system", "content": "You are an expert at extracting structured text from image documents."},
                {"role": "user", "content": input_data[0]["text_input"]},
            ]

            # Generate and process response
            prompt = apply_chat_template(processor, config, messages)  # Assuming defined
            response = generate(
                model,
                processor,
                image,
                prompt,
                resize_shape=(width, height),
                max_tokens=4000,
                temperature=0.0,
                verbose=False
            )
            results.append(self.process_response(response))

            print("Inference completed successfully for: ", file_path)

        return results

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