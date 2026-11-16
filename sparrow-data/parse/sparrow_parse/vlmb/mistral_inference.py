from mistralai.client import Mistral
from sparrow_parse.vlmb.inference_base import ModelInference
import os
import base64
import mimetypes
import time
import json, re
from rich import print


class MistralInference(ModelInference):
    """
    A class for performing inference using the Mistral cloud (EU endpoint by default).

    The model name decides the path:
      - OCR model (name contains "ocr", e.g. "mistral-ocr-4-1"): the image goes to the OCR endpoint and the
        result is returned as a list of elements [{"category": ..., "text": ...}], one entry per block.
      - Chat model (e.g. "mistral-small-2603"): the image and the prompt go directly to the chat endpoint,
        and the extracted JSON is returned.

    Usage statistics are collected in self.usage_log (one dict per call to Mistral) and accumulate across
    inference() calls until reset_usage_log() is called, see get_usage_log().
    """

    # Regional endpoint. Default is the EU endpoint; override with MISTRAL_SERVER_URL.
    # Global (no location commitment): https://api.mistral.ai
    DEFAULT_SERVER_URL = "https://api.eu.mistral.ai"

    # Mistral OCR block type -> element category
    CATEGORY_MAP = {
        "title": "Section-header",
        "text": "Text",
        "list": "List-item",
        "table": "Table",
        "image": "Picture",
        "equation": "Formula",
        "caption": "Caption",
        "header": "Page-header",
        "footer": "Page-footer",
    }

    def __init__(self, model_name):
        """
        Initialize the Mistral inference client.

        :param model_name: Identifier of the Mistral model to target for inference.
        :raises KeyError: If the MISTRAL_API_KEY environment variable is not set.
        """
        api_key = os.environ["MISTRAL_API_KEY"]
        self.model_name = model_name
        self.server_url = os.environ.get("MISTRAL_SERVER_URL", self.DEFAULT_SERVER_URL)
        self.client = Mistral(api_key=api_key, server_url=self.server_url)
        self.usage_log = []
        print("Mistral API key loaded for model: " + self.model_name)
        print("Mistral endpoint: " + self.server_url)


    def _is_ocr_model(self):
        """True if the configured model is an OCR model (uses the OCR endpoint, no prompt)."""
        return "ocr" in self.model_name.lower()


    def reset_usage_log(self):
        """Clear the usage log. The caller (VLLMExtractor.run_inference) resets it once per document."""
        self.usage_log = []


    def get_usage_log(self):
        """
        Usage statistics since the last reset_usage_log(), one dict per Mistral call (one per image).
        Intended for logging to the DB from the pipeline.

        Common keys: model, endpoint, call_type ("ocr" or "chat"), elapsed_seconds.
        OCR calls:  ocr_pages_processed, ocr_doc_size_bytes, ocr_confidence (page average, may be None).
        Chat calls: prompt_tokens (includes image tokens), completion_tokens, total_tokens.
        Values that the API does not return are None.
        """
        return list(self.usage_log)


    def _record_usage(self, call_type, elapsed, ocr_response=None, chat_response=None, file_path=None):
        """
        Build the usage dict of one Mistral call and append it to self.usage_log.

        :return: The usage dict.
        """
        stats = {
            "model": self.model_name,
            "endpoint": self.server_url,
            "call_type": call_type,
            "file": os.path.basename(file_path) if file_path else None,
            "elapsed_seconds": round(elapsed, 3),
        }

        if ocr_response is not None:
            usage_info = getattr(ocr_response, "usage_info", None)
            stats["ocr_pages_processed"] = getattr(usage_info, "pages_processed", None)
            stats["ocr_doc_size_bytes"] = getattr(usage_info, "doc_size_bytes", None)
            scores = [
                page.confidence_scores.average_page_confidence_score
                for page in ocr_response.pages
                if getattr(page, "confidence_scores", None)
            ]
            stats["ocr_confidence"] = round(sum(scores) / len(scores), 4) if scores else None

        if chat_response is not None:
            usage = getattr(chat_response, "usage", None)
            stats["prompt_tokens"] = getattr(usage, "prompt_tokens", None)
            stats["completion_tokens"] = getattr(usage, "completion_tokens", None)
            stats["total_tokens"] = getattr(usage, "total_tokens", None)

        self.usage_log.append(stats)
        return stats


    @staticmethod
    def encode_image(image_path):
        """Read an image file and return it as a base64 data URL."""
        mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime_type};base64,{image_data}"


    @staticmethod
    def normalize_table_html(html):
        """
        Normalize Mistral table HTML: <br/> and line breaks become spaces,
        the header row goes into <thead>, the rest into <tbody>.
        """
        html = re.sub(r"<br\s*/?>", " ", html)
        html = re.sub(r"\s+", " ", html).strip()
        match = re.match(r"^<table>(<tr>.*?</tr>)(.*)</table>$", html, re.DOTALL)
        if match and "<th>" in match.group(1):
            html = f"<table><thead>{match.group(1)}</thead><tbody>{match.group(2)}</tbody></table>"
        return html


    def blocks_to_elements(self, page):
        """
        Convert the Mistral OCR blocks of one page into a list of elements: {"category": ..., "text": ...}.
        Bounding boxes are not needed by the pipeline, so they are left out.
        """
        elements = []
        for block in page.blocks:
            text = block.content
            # With table_format="html", a table block's content is already the full table HTML
            if block.type == "table" and text:
                text = self.normalize_table_html(text)
            elements.append({
                "category": self.CATEGORY_MAP.get(block.type, block.type),
                "text": text
            })
        return elements


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
        Perform inference on input data using the configured Mistral model.

        :param input_data: A list of dictionaries containing image file paths and text inputs.
        :param apply_annotation: Not used for Mistral (bounding boxes are not returned).
        :param ocr_callback: Not used for Mistral (OCR is a separate model choice, not a chained step).
        :param mode: Optional mode for inference ("static" for simple JSON output).
        :return: List of processed model responses. Usage statistics: see get_usage_log().
        """
        # Handle static mode
        if mode == "static":
            return [self.get_simple_json()]

        # Determine if we're doing text-only or image-based inference
        is_text_only = input_data[0].get("file_path") is None

        if is_text_only:
            if self._is_ocr_model():
                raise ValueError("Text-only input is not supported with an OCR model: " + self.model_name)
            # Text-only inference
            messages = input_data[0]["text_input"]
            response = self._generate_text_response(messages)
            results = [response]
        else:
            # Image-based inference
            file_paths = self._extract_file_paths(input_data)
            prompt = input_data[0].get("text_input")
            results = self._process_images(file_paths, prompt)

        return results


    def _generate_text_response(self, messages):
        """
        Generate a text response with a Mistral chat model for text-only inputs.

        :param messages: Input messages
        :return: Generated response
        """
        start = time.perf_counter()
        chat_response = self.client.chat.complete(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": f"{messages}"
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        elapsed = time.perf_counter() - start

        self._record_usage("chat", elapsed, chat_response=chat_response)
        print("Inference completed successfully")
        return self.process_response(chat_response.choices[0].message.content)


    def _process_images(self, file_paths, prompt):
        """
        Process the images, one Mistral call per image, and collect the output.

        :param file_paths: List of absolute image file paths to process.
        :param prompt: Prompt/text input (used by chat models, OCR has no prompt).
        :return: List of per-image results.
        """
        results = []
        for file_path in file_paths:
            data_url = self.encode_image(file_path)

            if self._is_ocr_model():
                processed_response = self._run_ocr(file_path, data_url)
            else:
                processed_response = self._run_chat(file_path, data_url, prompt)

            results.append(processed_response)
            print(f"Inference completed successfully for: {file_path}")

        return results


    def _run_ocr(self, file_path, data_url):
        """
        Run Mistral OCR on one image. Returns a JSON string with a list of elements
        [{"category": ..., "text": ...}] for all pages (an image has one page).
        """
        start = time.perf_counter()
        ocr_response = self.client.ocr.process(
            model=self.model_name,
            document={
                "type": "image_url",
                "image_url": data_url
            },
            table_format="html",
            extract_footer=True,
            confidence_scores_granularity="page",
            include_blocks=True
        )
        elapsed = time.perf_counter() - start

        self._record_usage("ocr", elapsed, ocr_response=ocr_response, file_path=file_path)

        elements = []
        for page in ocr_response.pages:
            if not page.blocks:
                print(f"Warning: page {page.index} returned no blocks (needs OCR 4 or newer with include_blocks=True)")
                continue
            elements.extend(self.blocks_to_elements(page))

        return json.dumps(elements, indent=2, ensure_ascii=False)


    def _run_chat(self, file_path, data_url, prompt):
        """
        Send the image and the prompt directly to a Mistral chat model (no OCR step).
        Returns the extracted JSON as a string.
        """
        start = time.perf_counter()
        chat_response = self.client.chat.complete(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{prompt}"},
                        {"type": "image_url", "image_url": data_url}
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        elapsed = time.perf_counter() - start

        self._record_usage("chat", elapsed, chat_response=chat_response, file_path=file_path)

        return self.process_response(chat_response.choices[0].message.content)


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