import os
import base64
import json
import re
import time
import mimetypes
from rich import print
from rich.markup import escape
from mistralai.client import Mistral

# Mistral OCR block type -> element category (edit as needed)
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

DEFAULT_IMAGE = "images/bonds_table.png"
PROMPT = 'retrieve [{"instrument_name":"str", "valuation":"int"}]. return response in JSON format'

# Print the prompt before the chat call (debug)
SHOW_PROMPT = True

# Reasoning effort sent to the API. None = parameter not sent (the model default applies).
# Small 4: "none" or "high". Large 4: "low", "medium" or "high".
REASONING_EFFORT = "low"
# Print the model's thinking (only returned when reasoning is on)
SHOW_THINKING = True

# OCR + chat mode: also send the image to the chat model (False = the chat model gets the OCR text only)
OCR_CHAT_WITH_IMAGE = False

# Regional endpoint. Default is the EU endpoint; override with MISTRAL_SERVER_URL.
# Global (no location commitment): https://api.mistral.ai
SERVER_URL = os.environ.get("MISTRAL_SERVER_URL", "https://api.eu.mistral.ai")


def print_prompt(prompt):
    """Print the prompt before the chat call (debug)."""
    print(f"=== PROMPT ({len(prompt)} characters) ===")
    # escape(): the prompt contains square brackets, which rich would otherwise treat as markup
    print(escape(prompt))
    print("=== END OF PROMPT ===")


def encode_image(image_path):
    """Read an image file and return it as a base64 data URL."""
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{image_data}"


def normalize_table_html(html):
    """
    Normalize Mistral table HTML:
    <br/> and line breaks become spaces, header row goes into <thead>, the rest into <tbody>.
    """
    html = re.sub(r"<br\s*/?>", " ", html)
    html = re.sub(r"\s+", " ", html).strip()
    match = re.match(r"^<table>(<tr>.*?</tr>)(.*)</table>$", html, re.DOTALL)
    if match and "<th>" in match.group(1):
        html = f"<table><thead>{match.group(1)}</thead><tbody>{match.group(2)}</tbody></table>"
    return html


def blocks_to_elements(page):
    """
    Convert Mistral OCR blocks of one page into a list of elements:
    {"category": ..., "text": ...}. Bounding boxes are not needed by the pipeline, so they are left out.
    """
    elements = []
    for block in page.blocks:
        text = block.content
        # With table_format="html", a table block's content is already the full table HTML
        if block.type == "table" and text:
            text = normalize_table_html(text)
        elements.append({
            "category": CATEGORY_MAP.get(block.type, block.type),
            "text": text
        })
    return elements


def run_ocr(client, model, data_url):
    """
    Run Mistral OCR on the image and print the extracted elements, one list per page.
    Returns the list of per-page element lists. No extraction step.
    """
    ocr_response = client.ocr.process(
        model=model,
        document={
            "type": "image_url",
            "image_url": data_url
        },
        table_format="html",
        extract_footer=True,
        confidence_scores_granularity="page",
        include_blocks=True
    )

    # OCR is billed per page, not per token. Print everything the API returns in usage_info
    # (field names may differ by SDK version), so any token fields would show up here too.
    usage_info = getattr(ocr_response, "usage_info", None)
    if usage_info is not None:
        print(f"OCR pages processed: {getattr(usage_info, 'pages_processed', 'n/a')}")
        print(f"OCR usage_info: {usage_info}")

    results = []
    for page in ocr_response.pages:
        if page.confidence_scores:
            print(f"Page {page.index} confidence: {page.confidence_scores.average_page_confidence_score}")

        if not page.blocks:
            print(f"Page {page.index}: no blocks returned (needs OCR 4 or newer with include_blocks=True)")
            continue

        elements = blocks_to_elements(page)
        results.append(elements)

        print(f"=== EXTRACTED JSON, page {page.index + 1} ===")
        print(json.dumps(elements, indent=2, ensure_ascii=False))

    return results


def split_content(content):
    """
    Split message content into (answer_text, thinking_text).
    Without reasoning the content is a plain string; with reasoning it is a list of chunks
    (a thinking chunk and a text chunk).
    """
    if isinstance(content, str):
        return content, ""
    answer, thinking = [], []
    for chunk in content:
        kind = getattr(chunk, "type", None)
        if kind == "thinking":
            for part in getattr(chunk, "thinking", None) or []:
                thinking.append(getattr(part, "text", "") or "")
        elif kind == "text":
            answer.append(getattr(chunk, "text", "") or "")
    return "".join(answer), "".join(thinking)


def run_chat(client, model, data_url, prompt):
    """
    Send the prompt, and the image if data_url is given, to a Mistral chat model (e.g. Mistral Small).
    With data_url=None the call is text-only. Returns the extracted JSON.
    """
    content = [{"type": "text", "text": prompt}]
    if data_url:
        content.append({"type": "image_url", "image_url": data_url})

    extra_params = {}
    if REASONING_EFFORT:
        extra_params["reasoning_effort"] = REASONING_EFFORT

    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": content
            }
        ],
        response_format={"type": "json_object"},
        temperature=0,
        top_p=1,  # Large 4 rejects temperature=0 unless top_p is 1 (greedy sampling)
        **extra_params
    )

    # Token usage per call; prompt tokens include the image tokens
    usage = chat_response.usage
    print(f"Chat tokens: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}")

    answer, thinking = split_content(chat_response.choices[0].message.content)
    if SHOW_THINKING and thinking:
        print("=== THINKING ===")
        print(escape(thinking))
    result = json.loads(answer)
    print("=== EXTRACTED JSON ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def run_ocr_then_chat(client, ocr_model, chat_model, data_url, prompt):
    """
    Two steps: Mistral OCR reads the page, then a chat model extracts the JSON from the OCR text
    (and from the image too, if OCR_CHAT_WITH_IMAGE is True). The prompt is sent unchanged,
    the OCR text is appended after it. Returns the extracted JSON.
    """
    # Step 1: OCR
    ocr_start = time.perf_counter()
    ocr_response = client.ocr.process(
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
    ocr_elapsed = time.perf_counter() - ocr_start

    elements = []
    for page in ocr_response.pages:
        if page.confidence_scores:
            print(f"OCR page {page.index} confidence: {page.confidence_scores.average_page_confidence_score}")
        if not page.blocks:
            print(f"OCR page {page.index}: no blocks returned (needs OCR 4 or newer with include_blocks=True)")
            continue
        elements.extend(blocks_to_elements(page))

    if not elements:
        raise RuntimeError(f"OCR model {ocr_model} returned no text blocks, cannot run the chat step")

    usage_info = getattr(ocr_response, "usage_info", None)
    print(f"OCR: {len(elements)} blocks, pages processed: {getattr(usage_info, 'pages_processed', 'n/a')}, "
          f"time: {ocr_elapsed:.2f} s")

    ocr_text = json.dumps(elements, ensure_ascii=False)
    if SHOW_PROMPT:
        print("=== OCR TEXT SENT TO THE CHAT MODEL ===")
        print(escape(json.dumps(elements, indent=2, ensure_ascii=False)))
        print("=== END OF OCR TEXT ===")

    # Step 2: chat model, with the OCR text appended after the prompt
    chat_prompt = prompt + "\n\nDocument text extracted by OCR (JSON list of blocks):\n" + ocr_text
    chat_start = time.perf_counter()
    result = run_chat(client, chat_model, data_url if OCR_CHAT_WITH_IMAGE else None, chat_prompt)
    chat_elapsed = time.perf_counter() - chat_start
    print(f"Chat time: {chat_elapsed:.2f} s (image sent: {OCR_CHAT_WITH_IMAGE})")
    return result


def main():
    # Model to run: an OCR model (e.g. "mistral-ocr-4-1") or a chat model (e.g. "mistral-small-2603", "mistral-large-4")
    model = "mistral-large-4"
    # Optional OCR model. If set together with a chat model, OCR runs first and the chat model gets its text
    # (see OCR_CHAT_WITH_IMAGE). Set to None to send the image straight to the chat model.
    ocr_model = "mistral-ocr-4-1"
    image_path = DEFAULT_IMAGE

    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key, server_url=SERVER_URL)
    print(f"Using endpoint: {SERVER_URL}")
    print(f"Model: {model}, OCR model: {ocr_model}, image: {image_path}, "
          f"reasoning effort: {REASONING_EFFORT or 'API default'}")

    data_url = encode_image(image_path)

    # Time the inference call only (not client setup or image encoding)
    start = time.perf_counter()
    if "ocr" in model:
        run_ocr(client, model, data_url)
    else:
        if SHOW_PROMPT:
            print_prompt(PROMPT)
        if ocr_model:
            run_ocr_then_chat(client, ocr_model, model, data_url, PROMPT)
        else:
            run_chat(client, model, data_url, PROMPT)
    elapsed = time.perf_counter() - start
    print(f"Inference time: {elapsed:.2f} s")


if __name__ == "__main__":
    main()