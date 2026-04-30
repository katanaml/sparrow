"""Unit tests for the LiteLLM vision-LLM backend.

Tests run without external dependencies by mocking ``litellm.completion``.
Live integration is exercised via a separate scratch script (not part of
the suite).
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sparrow_parse.vlmb.litellm_inference import (
    LiteLLMInference,
    _file_to_data_uri,
)
from sparrow_parse.vlmb.inference_factory import InferenceFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_completion(content: str) -> SimpleNamespace:
    """Build a mock OpenAI-shaped litellm.completion return value."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def _make_temp_image() -> str:
    """Write a tiny PNG-like blob to a temp file and return the path."""
    fd, path = tempfile.mkstemp(suffix=".png")
    with os.fdopen(fd, "wb") as fh:
        # Minimal 1x1 PNG byte signature; content doesn't matter for tests.
        fh.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    return path


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestLiteLLMInit(unittest.TestCase):
    def test_drop_params_default_on(self):
        backend = LiteLLMInference("anthropic/claude-3-5-sonnet-20241022")
        self.assertIs(backend.default_kwargs.get("drop_params"), True)

    def test_drop_params_can_be_disabled(self):
        backend = LiteLLMInference(
            "anthropic/claude-3-5-sonnet-20241022",
            litellm_kwargs={"drop_params": False},
        )
        self.assertIs(backend.default_kwargs.get("drop_params"), False)

    def test_user_kwargs_merged_with_default(self):
        backend = LiteLLMInference(
            "openai/gpt-4o",
            litellm_kwargs={"num_retries": 3, "timeout": 120},
        )
        self.assertEqual(backend.default_kwargs.get("num_retries"), 3)
        self.assertEqual(backend.default_kwargs.get("timeout"), 120)
        # default still preserved
        self.assertIs(backend.default_kwargs.get("drop_params"), True)

    def test_call_kwargs_omits_unset_credentials(self):
        backend = LiteLLMInference("openai/gpt-4o")
        kwargs = backend._call_kwargs()
        self.assertNotIn("api_key", kwargs)
        self.assertNotIn("api_base", kwargs)

    def test_call_kwargs_includes_provided_credentials(self):
        backend = LiteLLMInference(
            "openai/gpt-4o",
            api_key="sk-test",
            api_base="https://example.invalid/v1",
        )
        kwargs = backend._call_kwargs()
        self.assertEqual(kwargs["api_key"], "sk-test")
        self.assertEqual(kwargs["api_base"], "https://example.invalid/v1")


# ---------------------------------------------------------------------------
# Factory registration
# ---------------------------------------------------------------------------


class TestFactoryRegistration(unittest.TestCase):
    def test_factory_returns_litellm_backend(self):
        factory = InferenceFactory(
            {"method": "litellm", "model_name": "openai/gpt-4o-mini"}
        )
        instance = factory.get_inference_instance()
        self.assertIsInstance(instance, LiteLLMInference)
        self.assertEqual(instance.model_name, "openai/gpt-4o-mini")

    def test_factory_passes_through_credentials(self):
        factory = InferenceFactory(
            {
                "method": "litellm",
                "model_name": "anthropic/claude-3-5-sonnet-20241022",
                "api_key": "sk-test",
                "api_base": "https://example.invalid/v1",
                "litellm_kwargs": {"num_retries": 5},
            }
        )
        instance = factory.get_inference_instance()
        self.assertEqual(instance.api_key, "sk-test")
        self.assertEqual(instance.api_base, "https://example.invalid/v1")
        self.assertEqual(instance.default_kwargs["num_retries"], 5)


# ---------------------------------------------------------------------------
# inference() — mode handling
# ---------------------------------------------------------------------------


class TestInferenceModes(unittest.TestCase):
    def test_static_mode_returns_sample_json(self):
        backend = LiteLLMInference("openai/gpt-4o-mini")
        result = backend.inference([{"text_input": "ignored"}], mode="static")
        self.assertEqual(len(result), 1)
        # Sample JSON has a 'table' key per inference_base.get_simple_json
        self.assertIn("table", json.loads(result[0]))

    def test_empty_input_raises(self):
        backend = LiteLLMInference("openai/gpt-4o-mini")
        with self.assertRaises(ValueError):
            backend.inference([])

    def test_text_only_dispatch(self):
        backend = LiteLLMInference("openai/gpt-4o-mini")
        with patch(
            "litellm.completion",
            return_value=_mock_completion('{"answer": "4"}'),
        ) as mock:
            result = backend.inference(
                [{"text_input": "what is 2+2?", "file_path": None}]
            )
        self.assertEqual(len(result), 1)
        # Result is the cleaned/parsed JSON
        self.assertEqual(json.loads(result[0]), {"answer": "4"})
        # litellm.completion was called once with the text content as a string,
        # confirming the text-only path was taken (not the image path).
        kwargs = mock.call_args.kwargs
        self.assertEqual(kwargs["model"], "openai/gpt-4o-mini")
        self.assertEqual(
            kwargs["messages"][0]["content"], "what is 2+2?"
        )
        self.assertIs(kwargs["drop_params"], True)


# ---------------------------------------------------------------------------
# Image dispatch
# ---------------------------------------------------------------------------


class TestImageInference(unittest.TestCase):
    def test_image_request_uses_data_uri(self):
        backend = LiteLLMInference("anthropic/claude-3-5-sonnet-20241022")
        img = _make_temp_image()
        try:
            with patch(
                "litellm.completion",
                return_value=_mock_completion('[{"name": "test"}]'),
            ) as mock:
                results = backend.inference(
                    [
                        {
                            "file_path": [img],
                            "text_input": "extract names as JSON list",
                        }
                    ]
                )
            self.assertEqual(len(results), 1)
            kwargs = mock.call_args.kwargs
            content_blocks = kwargs["messages"][0]["content"]
            self.assertEqual(content_blocks[0]["type"], "text")
            self.assertEqual(content_blocks[0]["text"], "extract names as JSON list")
            self.assertEqual(content_blocks[1]["type"], "image_url")
            url = content_blocks[1]["image_url"]["url"]
            self.assertTrue(url.startswith("data:image/png;base64,"))
        finally:
            os.unlink(img)

    def test_missing_image_skipped(self):
        backend = LiteLLMInference("openai/gpt-4o-mini")
        with patch("litellm.completion") as mock:
            results = backend.inference(
                [
                    {
                        "file_path": ["/nonexistent/path/that/does/not/exist.png"],
                        "text_input": "extract",
                    }
                ]
            )
        # No file means no upstream call and no result
        self.assertEqual(results, [])
        mock.assert_not_called()

    def test_image_failure_continues_with_other_files(self):
        backend = LiteLLMInference("openai/gpt-4o-mini")
        img1 = _make_temp_image()
        img2 = _make_temp_image()
        try:
            # First call fails, second succeeds
            with patch(
                "litellm.completion",
                side_effect=[
                    Exception("network blip"),
                    _mock_completion('{"ok": true}'),
                ],
            ):
                results = backend.inference(
                    [
                        {"file_path": [img1, img2], "text_input": "extract"},
                    ]
                )
            self.assertEqual(len(results), 1)
            self.assertEqual(json.loads(results[0]), {"ok": True})
        finally:
            os.unlink(img1)
            os.unlink(img2)


# ---------------------------------------------------------------------------
# process_response — JSON cleanup parity with sibling backends
# ---------------------------------------------------------------------------


class TestProcessResponse(unittest.TestCase):
    def setUp(self):
        self.backend = LiteLLMInference("openai/gpt-4o-mini")

    def test_strips_markdown_code_fence(self):
        raw = '```json\n{"a": 1}\n```'
        out = self.backend.process_response(raw)
        self.assertEqual(json.loads(out), {"a": 1})

    def test_extracts_embedded_json_array(self):
        raw = 'Here you go:\n[{"name": "Alice"}, {"name": "Bob"}]\nThanks.'
        out = self.backend.process_response(raw)
        self.assertEqual(
            json.loads(out), [{"name": "Alice"}, {"name": "Bob"}]
        )

    def test_returns_text_when_not_json(self):
        raw = "Plain text response"
        self.assertEqual(self.backend.process_response(raw), raw)


# ---------------------------------------------------------------------------
# data URI helper
# ---------------------------------------------------------------------------


class TestDataUri(unittest.TestCase):
    def test_data_uri_round_trip(self):
        path = _make_temp_image()
        try:
            uri = _file_to_data_uri(path)
            self.assertTrue(uri.startswith("data:image/png;base64,"))
            encoded = uri.split(",", 1)[1]
            with open(path, "rb") as fh:
                expected = fh.read()
            self.assertEqual(base64.b64decode(encoded), expected)
        finally:
            os.unlink(path)

    def test_data_uri_falls_back_for_unknown_extension(self):
        fd, path = tempfile.mkstemp(suffix=".weirdext")
        with os.fdopen(fd, "wb") as fh:
            fh.write(b"\x00\x01\x02")
        try:
            uri = _file_to_data_uri(path)
            # Falls back to image/png when mimetype can't be guessed
            self.assertTrue(uri.startswith("data:image/png;base64,"))
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
