import os
import base64
import json
from rich import print
from mistralai.client import Mistral

api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)

# Load and encode image
with open("images/bonds_table.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Step 1: OCR
ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "image_url",
        "image_url": f"data:image/png;base64,{image_data}"
    },
    table_format="html",
    extract_footer=True,
    confidence_scores_granularity="page"
)

# Collect markdown from all pages
markdown_text = ""
for page in ocr_response.pages:
    markdown_text += page.markdown + "\n"
    if page.footer:
        markdown_text += f"\nFOOTER: {page.footer}\n"
    if page.confidence_scores:
        print(f"Page {page.index} confidence: {page.confidence_scores.average_page_confidence_score}")
    if page.tables:
        for table in page.tables:
            markdown_text += f"\n{table.content}\n"

print("=== OCR OUTPUT ===")
print(markdown_text)

# Step 2: Structured extraction
prompt = 'retrieve [{"instrument_name":"str", "valuation":"int"}]. return response in JSON format'

chat_response = client.chat.complete(
    model="mistral-small-latest",
    messages=[
        {
            "role": "user",
            "content": f"{prompt}\n\n{markdown_text}"
        }
    ],
    response_format={"type": "json_object"}
)

print("=== EXTRACTED JSON ===")
print(json.dumps(json.loads(chat_response.choices[0].message.content), indent=2, ensure_ascii=False))