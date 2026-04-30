"""LiteLLM AI Gateway inference backend.

Routes every inference call through ``litellm.completion`` so a single Sparrow
backend can extract from images using OpenAI, Anthropic, Vertex AI, Bedrock,
Azure, Cohere, Mistral, Groq, and 90+ other vision-capable providers without
adding each SDK separately. The model is selected via the standard LiteLLM
provider-prefixed name (``anthropic/claude-3-5-sonnet-20241022``,
``vertex_ai/gemini-1.5-pro``, ``bedrock/anthropic.claude-3-5-sonnet-...``,
``azure/gpt-4o``, ``openai/gpt-4o``, ...) and credentials are resolved
either from provider-specific environment variables (``ANTHROPIC_API_KEY``,
``OPENAI_API_KEY``, ``AWS_ACCESS_KEY_ID``, ...) or from the optional
``api_key`` / ``api_base`` passed to the backend.

This is the *embedded* SDK form of LiteLLM. Sparrow imports the litellm
Python package directly. It does not require running a separate LiteLLM proxy
server.

``drop_params=True`` is enabled by default so kwargs that some providers
reject (``frequency_penalty`` / ``presence_penalty`` on Anthropic, Gemini,
Bedrock; ``response_format`` on Bedrock; etc.) are silently dropped instead
of raising ``UnsupportedParamsError``. Override via ``litellm_kwargs``.
"""

import base64
import json
import mimetypes
import os
import re

from sparrow_parse.vlmb.inference_base import ModelInference


class LiteLLMInference(ModelInference):
    """Vision-LLM backend that delegates to ``litellm.completion``."""

    def __init__(self, model_name, api_key=None, api_base=None, litellm_kwargs=None):
        """Initialize the LiteLLM inference backend.

        :param model_name: LiteLLM provider-prefixed model id, for example
            ``anthropic/claude-3-5-sonnet-20241022`` or
            ``vertex_ai/gemini-1.5-pro``. See https://docs.litellm.ai/docs/providers.
        :param api_key: Optional API key. When unset, LiteLLM resolves the
            provider-specific key from environment variables.
        :param api_base: Optional API base URL, only needed for OpenAI-compatible
            custom endpoints (private LiteLLM proxies, Azure deployments, etc.).
        :param litellm_kwargs: Optional dict of extra kwargs forwarded to every
            ``litellm.completion`` call. ``drop_params=True`` is set by default
            and merged with anything passed here.
        """
        try:
            import litellm  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "litellm is required for LiteLLMInference. "
                'Install via `pip install "litellm>=1.60,<1.85"` '
                'or `pip install "sparrow-parse[litellm]"`.'
            ) from exc

        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base

        merged = {"drop_params": True}
        if litellm_kwargs and isinstance(litellm_kwargs, dict):
            merged.update(litellm_kwargs)
        self.default_kwargs = merged

        print(f"LiteLLM initialized for model: {model_name}")

    def process_response(self, output_text):
        """Process and clean the model's raw output as JSON or markdown/text.

        Mirrors the helper in ``ollama_inference.py`` / ``vllm_inference.py``
        so callers see consistent output regardless of backend.
        """
        try:
            if "```" in output_text:
                json_start = output_text.find("```json")
                if json_start != -1:
                    content = output_text[json_start + 7:]
                    json_end = content.rfind("```")
                    if json_end != -1:
                        content = content[:json_end].strip()
                        formatted_json = json.loads(content)
                        return json.dumps(formatted_json, indent=2, ensure_ascii=False)
                else:
                    return output_text

            for pattern in [r"\[\s*\{.*\}\s*\]", r"\{.*\}"]:
                matches = re.search(pattern, output_text, re.DOTALL)
                if matches:
                    potential_json = matches.group(0)
                    try:
                        formatted_json = json.loads(potential_json)
                        return json.dumps(formatted_json, indent=2, ensure_ascii=False)
                    except Exception:
                        pass

            formatted_json = json.loads(output_text.strip())
            return json.dumps(formatted_json, indent=2, ensure_ascii=False)

        except (json.JSONDecodeError, ValueError):
            return output_text
        except Exception:
            return output_text

    def inference(self, input_data, apply_annotation=False, ocr_callback=None, mode=None):
        """Perform inference on input data using the configured LiteLLM model.

        :param input_data: A list of dictionaries containing image file paths
            and text inputs (same shape as the other vlmb backends).
        :param apply_annotation: Optional flag to apply annotations to the
            output. Not supported on the LiteLLM backend (ignored).
        :param ocr_callback: Optional callback function to modify input data
            before inference.
        :param mode: Optional mode for inference. ``"static"`` returns a fixed
            sample JSON for testing without an upstream call.
        :return: List of processed model responses.
        """
        if not input_data or not isinstance(input_data, list) or len(input_data) == 0:
            raise ValueError("input_data must be a non-empty list")

        # Annotations are not supported on this backend.
        apply_annotation = False

        if mode == "static":
            return [self.get_simple_json()]

        is_text_only = input_data[0].get("file_path") is None

        if is_text_only:
            text = input_data[0]["text_input"]
            return [self._generate_text_response(text)]

        file_paths = self._extract_file_paths(input_data)
        return self._process_images(file_paths, input_data, ocr_callback)

    def _generate_text_response(self, text):
        """Generate a text-only response."""
        import litellm

        try:
            response = litellm.completion(
                model=self.model_name,
                messages=[{"role": "user", "content": text}],
                **self._call_kwargs(),
            )
            content = response.choices[0].message.content or ""
            print("Inference completed successfully")
            return self.process_response(content)
        except Exception as e:
            print(f"Error during text inference: {e}")
            raise

    def _process_images(self, file_paths, input_data, ocr_callback):
        """Process each image and produce a response."""
        import litellm

        results = []
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    print(f"Warning: File does not exist: {file_path}")
                    continue

                text = self._prepare_text(file_path, input_data, ocr_callback)
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text},
                            {
                                "type": "image_url",
                                "image_url": {"url": _file_to_data_uri(file_path)},
                            },
                        ],
                    }
                ]

                response = litellm.completion(
                    model=self.model_name,
                    messages=messages,
                    **self._call_kwargs(),
                )
                raw = response.choices[0].message.content or ""
                results.append(self.process_response(raw))
                print(f"Inference completed successfully for: {file_path}")
            except Exception as e:
                print(f"Error processing image {file_path}: {e}")
                # Match the resilience model used by ollama_inference: log the
                # failure for one image and keep going, rather than aborting
                # the whole batch.
                continue

        return results

    def _call_kwargs(self):
        """Build the kwargs dict for litellm.completion, including credentials."""
        kwargs = dict(self.default_kwargs)
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base
        return kwargs

    @staticmethod
    def _prepare_text(file_path, input_data, ocr_callback):
        """Run the optional OCR callback and pull the text input out."""
        if ocr_callback is not None:
            input_data = ocr_callback(file_path, input_data)
        return input_data[0]["text_input"]

    @staticmethod
    def _extract_file_paths(input_data):
        """Resolve absolute file paths from input data (matches ollama_inference)."""
        return [
            os.path.abspath(file_path)
            for data in input_data
            for file_path in data.get("file_path", [])
        ]


def _file_to_data_uri(path):
    """Read a local image / PDF file and return a base64 data URI.

    LiteLLM normalizes OpenAI-format ``image_url`` content blocks into each
    upstream provider's native shape (Anthropic ``image`` blocks, Bedrock
    ``image`` blocks, Vertex AI ``inlineData``, etc.), so a single data URI
    works across providers.
    """
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        # Reasonable default for image files without a recognised extension.
        mime = "image/png"
    with open(path, "rb") as fh:
        data = fh.read()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"
