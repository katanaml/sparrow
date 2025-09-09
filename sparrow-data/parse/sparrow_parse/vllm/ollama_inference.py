from sparrow_parse.vllm.inference_base import ModelInference


class OllamaInference(ModelInference):
    """
        A class for performing inference using the Ollama model.
        Handles image preprocessing, response formatting, and model interaction.
        """

    def __init__(self, model_name):
        """
        Initialize the inference class with the given model name.

        :param model_name: Name of the model to load.
        """
        self.model_name = model_name
        print(f"Ollama initialized for model: {model_name}")


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

        return '{}'