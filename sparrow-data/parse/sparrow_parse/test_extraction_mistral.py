import os
import base64
import json
import re
import time
import mimetypes
from rich import print
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

# Regional endpoint. Default is the EU endpoint; override with MISTRAL_SERVER_URL.
# Global (no location commitment): https://api.mistral.ai
SERVER_URL = os.environ.get("MISTRAL_SERVER_URL", "https://api.eu.mistral.ai")


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


def run_chat(client, model, data_url, prompt):
    """
    Send the image and the prompt directly to a Mistral chat model (e.g. Mistral Small). Returns the extracted JSON.
    """
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": data_url}
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    # Token usage per call; prompt tokens include the image tokens
    usage = chat_response.usage
    print(f"Chat tokens: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}")

    result = json.loads(chat_response.choices[0].message.content)
    print("=== EXTRACTED JSON ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main():
    # Model to run: an OCR model (e.g. "mistral-ocr-4-1") or a chat model (e.g. "mistral-small-2603")
    model = "mistral-small-2603"
    image_path = DEFAULT_IMAGE

    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key, server_url=SERVER_URL)
    print(f"Using endpoint: {SERVER_URL}")
    print(f"Model: {model}, image: {image_path}")

    data_url = encode_image(image_path)

    # Time the inference call only (not client setup or image encoding)
    start = time.perf_counter()
    if "ocr" in model:
        run_ocr(client, model, data_url)
    else:
        run_chat(client, model, data_url, PROMPT)
    elapsed = time.perf_counter() - start
    print(f"Inference time: {elapsed:.2f} s")


if __name__ == "__main__":
    main()