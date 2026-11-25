from mistralai.client import Mistral
from sparrow_parse.vlmb.inference_base import ModelInference
from concurrent.futures import ThreadPoolExecutor
import os
import base64
import mimetypes
import time
import json, re
from rich import print
from rich.markup import escape


class MistralInference(ModelInference):
    """
    A class for performing inference using the Mistral cloud (EU endpoint by default).

    Three modes, decided by the models passed in:
      - OCR model only (name contains "ocr", e.g. "mistral-ocr-4-1"): the image goes to the OCR endpoint and
        the result is returned as a list of elements [{"category": ..., "text": ...}], one entry per block.
      - Chat model only (e.g. "mistral-small-2603"): the image and the prompt go directly to the chat endpoint,
        and the extracted JSON is returned.
      - OCR model + chat model: OCR reads the page first, then the chat model extracts the JSON from the OCR
        text only (no image). The prompt and hints are sent unchanged, the OCR text is appended after them.

    Several images (pages) are processed in parallel, the results keep the order of the images.
    A failed OCR or chat call raises an error for the whole document.

    Settings from the environment:
      MISTRAL_API_KEY      (required)
      MISTRAL_SERVER_URL   (optional, default is the EU endpoint)
      MISTRAL_MAX_WORKERS  (optional, pages processed in parallel, default 4)
      MISTRAL_SHOW_PROMPT  (optional, 1/true/yes/on: print the text sent to the chat model, for debugging)
      MISTRAL_SHOW_THINKING (optional, 1/true/yes/on: print the chat model's thinking, for debugging)

    Usage statistics are collected in self.usage_log (one dict per call to Mistral, in page order) and
    accumulate across inference() calls until reset_usage_log() is called, see get_usage_log().
    """

    # Regional endpoint. Default is the EU endpoint; override with MISTRAL_SERVER_URL.
    # Global (no location commitment): https://api.mistral.ai
    DEFAULT_SERVER_URL = "https://api.eu.mistral.ai"

    # Pages processed in parallel. Override with MISTRAL_MAX_WORKERS.
    DEFAULT_MAX_WORKERS = 4

    # Added to the prompt in the OCR + chat mode, followed by the OCR text
    OCR_TEXT_HEADER = "\n\nDocument text extracted by OCR (JSON list of blocks):\n"

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

    def __init__(self, model_name, ocr_model_name=None):
        """
        Initialize the Mistral inference client.

        :param model_name: The Mistral model: a chat model, or an OCR model for OCR-only use.
        :param ocr_model_name: Optional OCR model. If set, model_name must be a chat model, and the OCR text
                               of each page is sent to it instead of the image.
        :raises KeyError: If the MISTRAL_API_KEY environment variable is not set.
        :raises ValueError: If the models do not fit together, or MISTRAL_MAX_WORKERS is not a positive number.
        """
        api_key = os.environ["MISTRAL_API_KEY"]
        self.model_name = model_name
        self.ocr_model_name = ocr_model_name

        if ocr_model_name:
            if self._is_ocr_name(model_name):
                raise ValueError("With an OCR model, the other model must be a chat model, got: " + model_name)
            if not self._is_ocr_name(ocr_model_name):
                raise ValueError("Not an OCR model: " + ocr_model_name)

        # Large models run with low reasoning: the accuracy is the same as with the default, but faster
        self.reasoning_effort = "low" if "large" in model_name.lower() else None

        self.server_url = os.environ.get("MISTRAL_SERVER_URL", self.DEFAULT_SERVER_URL)
        self.max_workers = self._read_max_workers()
        self.show_prompt = self._read_flag("MISTRAL_SHOW_PROMPT")
        self.show_thinking = self._read_flag("MISTRAL_SHOW_THINKING")
        self.client = Mistral(api_key=api_key, server_url=self.server_url)
        self.usage_log = []
        print("Mistral API key loaded for model: " + self.model_name)
        if self.ocr_model_name:
            print("Mistral OCR model: " + self.ocr_model_name)
        print("Mistral endpoint: " + self.server_url + ", parallel pages: " + str(self.max_workers))


    @classmethod
    def _read_max_workers(cls):
        """Read MISTRAL_MAX_WORKERS (positive integer), default 4."""
        value = os.environ.get("MISTRAL_MAX_WORKERS")
        if not value:
            return cls.DEFAULT_MAX_WORKERS
        try:
            workers = int(value)
        except ValueError:
            workers = 0
        if workers < 1:
            raise ValueError("MISTRAL_MAX_WORKERS must be a positive integer, got: " + value)
        return workers


    @staticmethod
    def _read_flag(name):
        """Read an on/off shell variable: 1, true, yes or on (any case) means on, unset or anything else is off."""
        return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


    @staticmethod
    def _is_ocr_name(name):
        """True if the model name is an OCR model (uses the OCR endpoint, no prompt)."""
        return "ocr" in name.lower()


    def _is_ocr_model(self):
        """True if the configured model is an OCR model used on its own (OCR only, no chat model)."""
        return self._is_ocr_name(self.model_name)


    def reset_usage_log(self):
        """Clear the usage log. The caller (VLLMExtractor.run_inference) resets it once per document."""
        self.usage_log = []


    def get_usage_log(self):
        """
        Usage statistics since the last reset_usage_log(), one dict per Mistral call, in page order
        (in the OCR + chat mode an OCR entry followed by its chat entry, for every page).
        Intended for logging to the DB from the pipeline.

        Common keys: model, endpoint, call_type ("ocr" or "chat"), file, elapsed_seconds.
        OCR calls:  ocr_pages_processed, ocr_doc_size_bytes, ocr_confidence (page average, may be None).
        Chat calls: prompt_tokens (includes image tokens), completion_tokens (includes reasoning tokens),
                    total_tokens.
        Values that the API does not return are None.
        """
        return list(self.usage_log)


    def _build_usage(self, call_type, model, elapsed, ocr_response=None, chat_response=None, file_path=None):
        """
        Build the usage dict of one Mistral call. It is returned, not stored: the pages run in parallel,
        so the entries are collected in page order after all pages are done.
        """
        stats = {
            "model": model,
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


    @staticmethod
    def split_content(content):
        """
        Split chat message content into (answer_text, thinking_text).
        Without reasoning the content is a plain string; with reasoning it is a list of chunks
        (a thinking chunk and a text chunk).
        """
        if isinstance(content, str):
            return content, ""
        answer, thinking = [], []
        for chunk in content or []:
            kind = getattr(chunk, "type", None)
            if kind == "thinking":
                for part in getattr(chunk, "thinking", None) or []:
                    thinking.append(getattr(part, "text", "") or "")
            elif kind == "text":
                answer.append(getattr(chunk, "text", "") or "")
        return "".join(answer), "".join(thinking)


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
        Perform inference on input data using the configured Mistral model(s).

        :param input_data: A list of dictionaries containing image file paths and text inputs.
        :param apply_annotation: Not used for Mistral (bounding boxes are not returned).
        :param ocr_callback: Not used for Mistral (OCR is a model choice, not a chained callback).
        :param mode: Optional mode for inference ("static" for simple JSON output).
        :return: List of processed model responses, in the order of the images.
                 Usage statistics: see get_usage_log().
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


    def _chat(self, content, label=None):
        """
        One chat call. Returns (answer_text, chat_response). The answer is the JSON text without the model's
        thinking. temperature=0 needs top_p=1 on Large models (greedy sampling).

        :param content: The message content (text, or a list of text/image parts).
        :param label: Name shown in the debug output (the file name), as pages run in parallel.
        """
        if self.show_prompt:
            if isinstance(content, str):
                prompt_text = content
            else:
                prompt_text = "\n".join(part["text"] for part in content if part.get("type") == "text")
            # One print call per block, so the output of parallel pages is not mixed line by line
            # escape(): the prompt contains square brackets, which rich would otherwise treat as markup
            print(f"=== PROMPT SENT TO {self.model_name}, {label} ({len(prompt_text)} characters) ===\n"
                  f"{escape(prompt_text)}\n=== END OF PROMPT ===")

        params = {}
        if self.reasoning_effort:
            params["reasoning_effort"] = self.reasoning_effort

        chat_response = self.client.chat.complete(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            response_format={"type": "json_object"},
            temperature=0,
            top_p=1,
            **params
        )
        answer, thinking = self.split_content(chat_response.choices[0].message.content)
        if self.show_thinking:
            print(f"=== THINKING, {label} ===\n{escape(thinking) if thinking else '(none returned)'}\n"
                  f"=== END OF THINKING ===")
        return answer, chat_response


    def _generate_text_response(self, messages):
        """
        Generate a text response with a Mistral chat model for text-only inputs.

        :param messages: Input messages
        :return: Generated response
        """
        start = time.perf_counter()
        answer, chat_response = self._chat(f"{messages}", label="text only")
        elapsed = time.perf_counter() - start

        self.usage_log.append(self._build_usage("chat", self.model_name, elapsed, chat_response=chat_response))
        print("Inference completed successfully")
        return self.process_response(answer)


    def _process_images(self, file_paths, prompt):
        """
        Process the images (pages) in parallel, one worker per image, and collect the output.
        The results and the usage entries keep the order of file_paths. If any page fails, the error is raised
        and the document fails.

        :param file_paths: List of absolute image file paths to process.
        :param prompt: Prompt/text input (used by chat models, OCR has no prompt).
        :return: List of per-image results, in the order of file_paths.
        """
        def process_one(file_path):
            result, usage = self._process_one_image(file_path, prompt)
            print(f"Inference completed successfully for: {file_path}")
            return result, usage

        workers = min(self.max_workers, len(file_paths))
        if workers <= 1:
            outcomes = [process_one(file_path) for file_path in file_paths]
        else:
            # map() returns the results in the order of the input, not in the order of completion
            with ThreadPoolExecutor(max_workers=workers) as executor:
                outcomes = list(executor.map(process_one, file_paths))

        results = []
        for result, usage in outcomes:
            results.append(result)
            self.usage_log.extend(usage)
        return results


    def _process_one_image(self, file_path, prompt):
        """
        Run the configured mode on one image. Runs in a worker thread, so it does not touch shared state.

        :return: (result, usage_entries) where usage_entries is the list of usage dicts of this image.
        """
        data_url = self.encode_image(file_path)

        if self._is_ocr_model():
            return self._run_ocr_only(file_path, data_url)
        if self.ocr_model_name:
            return self._run_ocr_then_chat(file_path, data_url, prompt)
        return self._run_chat(file_path, data_url, prompt)


    def _call_ocr(self, ocr_model, data_url):
        """
        Call Mistral OCR on one image. Returns (ocr_response, elements, elapsed_seconds), where elements is the
        list of {"category": ..., "text": ...} for all pages (an image has one page).
        """
        start = time.perf_counter()
        ocr_response = self.client.ocr.process(
            model=ocr_model,
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

        elements = []
        for page in ocr_response.pages:
            if not page.blocks:
                print(f"Warning: page {page.index} returned no blocks (needs OCR 4 or newer with include_blocks=True)")
                continue
            elements.extend(self.blocks_to_elements(page))

        return ocr_response, elements, elapsed


    def _run_ocr_only(self, file_path, data_url):
        """
        OCR only. Returns a JSON string with a list of elements [{"category": ..., "text": ...}].
        """
        ocr_response, elements, elapsed = self._call_ocr(self.model_name, data_url)
        usage = self._build_usage("ocr", self.model_name, elapsed, ocr_response=ocr_response, file_path=file_path)
        return json.dumps(elements, indent=2, ensure_ascii=False), [usage]


    def _run_chat(self, file_path, data_url, prompt):
        """
        Send the image and the prompt directly to a Mistral chat model (no OCR step).
        Returns the extracted JSON as a string.
        """
        start = time.perf_counter()
        answer, chat_response = self._chat([
            {"type": "text", "text": f"{prompt}"},
            {"type": "image_url", "image_url": data_url}
        ], label=os.path.basename(file_path))
        elapsed = time.perf_counter() - start

        usage = self._build_usage("chat", self.model_name, elapsed, chat_response=chat_response, file_path=file_path)
        return self.process_response(answer), [usage]


    def _run_ocr_then_chat(self, file_path, data_url, prompt):
        """
        Two steps: Mistral OCR reads the page, then the chat model extracts the JSON from the OCR text
        (the image is not sent to the chat model). The prompt and the hints are unchanged, the OCR text
        is appended after them. Returns the extracted JSON as a string.
        """
        ocr_response, elements, ocr_elapsed = self._call_ocr(self.ocr_model_name, data_url)
        ocr_usage = self._build_usage("ocr", self.ocr_model_name, ocr_elapsed, ocr_response=ocr_response,
                                      file_path=file_path)

        if not elements:
            raise RuntimeError(f"OCR model {self.ocr_model_name} returned no text blocks for {file_path}, "
                               "cannot run the chat step")

        chat_prompt = f"{prompt}" + self.OCR_TEXT_HEADER + json.dumps(elements, ensure_ascii=False)

        start = time.perf_counter()
        answer, chat_response = self._chat([{"type": "text", "text": chat_prompt}],
                                           label=os.path.basename(file_path))
        chat_elapsed = time.perf_counter() - start

        chat_usage = self._build_usage("chat", self.model_name, chat_elapsed, chat_response=chat_response,
                                       file_path=file_path)
        return self.process_response(answer), [ocr_usage, chat_usage]


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