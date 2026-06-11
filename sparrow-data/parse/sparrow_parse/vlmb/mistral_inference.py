from mistralai.client import Mistral
from sparrow_parse.vlmb.inference_base import ModelInference
import os
import base64
import json, re
from rich import print


class MistralInference(ModelInference):
    """
        A class for performing inference using the Mistral cloud.
        """

    def __init__(self, model_name):
        """
        Initialize the Mistral inference client.

        :param model_name: Identifier of the Mistral model to target for inference.
        :raises KeyError: If the MISTRAL_API_KEY environment variable is not set.
        """
        api_key = os.environ["MISTRAL_API_KEY"]
        self.model_name = model_name
        self.client = Mistral(api_key=api_key)
        print("Mistral API key loaded for model: " + self.model_name)


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
        Perform inference on input data using the specified Mistral model.

        :param input_data: A list of dictionaries containing image file paths and text inputs.
        :param apply_annotation: Optional flag to apply annotations to the output.
        :param ocr_callback: Optional callback function to modify input data before inference.
        :param mode: Optional mode for inference ("static" for simple JSON output).
        :return: List of processed model responses.
        """
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
            messages = input_data[0]["text_input"]
            results = self._process_images(file_paths, messages, apply_annotation, ocr_callback)

        return results


    def _generate_text_response(self, messages):
        """
        Generate a text response with Mistral for text-only inputs.

        :param messages: Input messages
        :return: Generated response
        """

        prompt = messages

        chat_response = self.client.chat.complete(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}"
                }
            ],
            response_format={"type": "json_object"}
        )

        print("Inference completed successfully")
        return self.process_response(chat_response.choices[0].message.content)


    def _process_images(self, file_paths, messages, apply_annotation, ocr_callback):
        """
        Run Mistral on each image and collect the output.

        :param file_paths: List of absolute image file paths to process.
        :param messages: Prompt/text input associated with the request.
        :param apply_annotation: Flag reserved for annotation output (currently unused).
        :param ocr_callback: Optional callback for post-processing OCR output (currently unused).
        :return: List of per-image results.
        """

        results = []
        for file_path in file_paths:
            # Load and encode image
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Step 1: OCR
            ocr_response = self.client.ocr.process(
                model=self.model_name,
                document={
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{image_data}"
                },
                table_format="html",
                extract_footer=True,
                confidence_scores_granularity="page"
            )

            # Collect markdown from page
            markdown_text = ""
            for page in ocr_response.pages:
                markdown_text += page.markdown + "\n"
                if page.footer:
                    markdown_text += f"\nFOOTER: {page.footer}\n"
                if page.confidence_scores:
                    pass
                    # print(f"Page {page.index} confidence: {page.confidence_scores.average_page_confidence_score}")
                if page.tables:
                    for table in page.tables:
                        markdown_text += f"\n{table.content}\n"

            print("Mistral OCR step completed")
            # Step 2: Structured extraction
            prompt = messages

            chat_response = self.client.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {
                        "role": "user",
                        "content": f"{prompt}\n\n{markdown_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )

            # Process the raw response
            processed_response = self.process_response(chat_response.choices[0].message.content)
            results.append(processed_response)
            print(f"Inference completed successfully for: {file_path}")

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