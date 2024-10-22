import gradio as gr
import requests
import os
from PIL import Image
import json
from datetime import datetime


# Example data with placeholder JSON for lab_results and bank_statement
examples = [
    ["bonds_table.png", "Bonds table", "[{\"instrument_name\":\"example\", \"valuation\":0}]"],
    ["lab_results.png", "Lab results", "{\"patient_name\": \"example\", \"patient_age\": \"example\", \"patient_pid\": 0, \"lab_results\": [{\"investigation\": \"example\", \"result\": 0.00, \"reference_value\": \"example\", \"unit\": \"example\"}]}"],
    ["bank_statement.png", "Bank statement", "*"]
]

# JSON data for Bonds table
bonds_json = [
    {
        "instrument_name": "UNITS BLACKROCK FIX INC DUB FDS PLC ISHS EUR INV GRD CP BD IDX/INST/E",
        "valuation": 19049
    },
    {
        "instrument_name": "UNITS ISHARES III PLC CORE EUR GOVT BOND UCITS ETF/EUR",
        "valuation": 83488
    },
    {
        "instrument_name": "UNITS ISHARES III PLC EUR CORP BOND 1-5YR UCITS ETF/EUR",
        "valuation": 213030
    },
    {
        "instrument_name": "UNIT ISHARES VI PLC/JP MORGAN USD E BOND EUR HED UCITS ETF DIST/HDGD/",
        "valuation": 32774
    },
    {
        "instrument_name": "UNITS XTRACKERS II SICAV/EUR HY CORP BOND UCITS ETF/-1D-/DISTR.",
        "valuation": 23643
    }
]

lab_results_json = {
    "patient_name": "Yash M. Patel",
    "patient_age": "21 Years",
    "patient_pid": 555,
    "lab_results": [
        {
          "investigation": "Hemoglobin (Hb)",
          "result": 12.5,
          "reference_value": "13.0 - 17.0",
          "unit": "g/dL"
        },
        {
          "investigation": "RBC COUNT",
          "result": 5.2,
          "reference_value": "4.5 - 5.5",
          "unit": "mill/cumm"
        },
        {
          "investigation": "Packed Cell Volume (PCV)",
          "result": 57.5,
          "reference_value": "40 - 50",
          "unit": "%"
        },
        {
          "investigation": "Mean Corpuscular Volume (MCV)",
          "result": 87.75,
          "reference_value": "83 - 101",
          "unit": "fL"
        },
        {
          "investigation": "MCH",
          "result": 27.2,
          "reference_value": "27 - 32",
          "unit": "pg"
        },
        {
          "investigation": "MCHC",
          "result": 32.8,
          "reference_value": "32.5 - 34.5",
          "unit": "g/dL"
        },
        {
          "investigation": "RDW",
          "result": 13.6,
          "reference_value": "11.6 - 14.0",
          "unit": "%"
        },
        {
          "investigation": "WBC COUNT",
          "result": 9000,
          "reference_value": "4000-11000",
          "unit": "cumm"
        },
        {
          "investigation": "Neutrophils",
          "result": 60,
          "reference_value": "50 - 62",
          "unit": "%"
        },
        {
          "investigation": "Lymphocytes",
          "result": 31,
          "reference_value": "20 - 40",
          "unit": "%"
        },
        {
          "investigation": "Eosinophils",
          "result": 1,
          "reference_value": "00 - 06",
          "unit": "%"
        },
        {
          "investigation": "Monocytes",
          "result": 7,
          "reference_value": "00 - 10",
          "unit": "%"
        },
        {
          "investigation": "Basophils",
          "result": 1,
          "reference_value": "00 - 02",
          "unit": "%"
        },
        {
          "investigation": "Absolute Neutrophils",
          "result": 6000,
          "reference_value": "1500 - 7500",
          "unit": "cells/mcL"
        },
        {
          "investigation": "Absolute Lymphocytes",
          "result": 3100,
          "reference_value": "1300 - 3500",
          "unit": "cells/mcL"
        },
        {
          "investigation": "Absolute Eosinophils",
          "result": 100,
          "reference_value": "00 - 500",
          "unit": "cells/mcL"
        },
        {
          "investigation": "Absolute Monocytes",
          "result": 700,
          "reference_value": "200 - 950",
          "unit": "cells/mcL"
        },
        {
          "investigation": "Absolute Basophils",
          "result": 100,
          "reference_value": "00 - 300",
          "unit": "cells/mcL"
        },
        {
          "investigation": "Platelet Count",
          "result": 320000,
          "reference_value": "150000 - 410000",
          "unit": "cumm"
        }
    ]
}

bank_statement_json = {
  "bank": "First Platypus Bank",
  "address": "1234 Kings St., New York, NY 12123",
  "account_holder": "Mary G. Orta",
  "account_number": "1234567890123",
  "statement_date": "3/1/2022",
  "period_covered": "2/1/2022 - 3/1/2022",
  "account_summary": {
    "balance_on_march_1": "$25,032.23",
    "total_money_in": "$10,234.23",
    "total_money_out": "$10,532.51"
  },
  "transactions": [
    {
      "date": "02/01",
      "description": "PGD EasyPay Debit",
      "withdrawal": "203.24",
      "deposit": "",
      "balance": "22,098.23"
    },
    {
      "date": "02/02",
      "description": "AB&B Online Payment*****",
      "withdrawal": "71.23",
      "deposit": "",
      "balance": "22,027.00"
    },
    {
      "date": "02/04",
      "description": "Check No. 2345",
      "withdrawal": "",
      "deposit": "450.00",
      "balance": "22,477.00"
    },
    {
      "date": "02/05",
      "description": "Payroll Direct Dep 23422342 Giants",
      "withdrawal": "",
      "deposit": "2,534.65",
      "balance": "25,011.65"
    },
    {
      "date": "02/06",
      "description": "Signature POS Debit - TJP",
      "withdrawal": "84.50",
      "deposit": "",
      "balance": "24,927.15"
    },
    {
      "date": "02/07",
      "description": "Check No. 234",
      "withdrawal": "1,400.00",
      "deposit": "",
      "balance": "23,527.15"
    },
    {
      "date": "02/08",
      "description": "Check No. 342",
      "withdrawal": "",
      "deposit": "25.00",
      "balance": "23,552.15"
    },
    {
      "date": "02/09",
      "description": "FPB AutoPay***** Credit Card",
      "withdrawal": "456.02",
      "deposit": "",
      "balance": "23,096.13"
    },
    {
      "date": "02/08",
      "description": "Check No. 123",
      "withdrawal": "",
      "deposit": "25.00",
      "balance": "23,552.15"
    },
    {
      "date": "02/09",
      "description": "FPB AutoPay***** Credit Card",
      "withdrawal": "156.02",
      "deposit": "",
      "balance": "23,096.13"
    },
    {
      "date": "02/08",
      "description": "Cash Deposit",
      "withdrawal": "",
      "deposit": "25.00",
      "balance": "23,552.15"
    }
  ]
}


def run_inference(image_filepath, query, key):
    if image_filepath is None:
        return {"error": f"No image provided. Please upload an image before submitting."}

    if query is None or query.strip() == "":
        return {"error": f"No query provided. Please enter a query before submitting."}

    if key is None or key.strip() == "":
        return {"error": f"No Sparrow Key provided. Please enter a Sparrow Key before submitting."}

    file_path = None
    try:
        # Open the uploaded image using its filepath
        img = Image.open(image_filepath)

        # Extract the file extension from the uploaded file
        input_image_extension = image_filepath.split('.')[-1].lower()  # Extract extension from filepath

        # Set file extension based on the original file, otherwise default to PNG
        if input_image_extension in ['jpg', 'jpeg', 'png']:
            file_extension = input_image_extension
        else:
            file_extension = 'png'  # Default to PNG if extension is unavailable or invalid

        # Generate a unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.{file_extension}"

        # Save the image
        img.save(filename)

        # Get the full path of the saved image
        file_path = os.path.abspath(filename)

        # Prepare the REST API call
        url = 'https://katanaml-sparrow-ml.hf.space/api/v1/sparrow-llm/inference'
        headers = {
            'accept': 'application/json'
        }

        # Open the file in binary mode and send it
        with open(filename, "rb") as f:
            files = {
                'file': (filename, f, f'image/{file_extension}')
            }

            # Convert 'query' input to JSON string if needed
            try:
                # Check if the query is a wildcard '*'
                if query.strip() == "*":
                    query_json = "*"  # Directly use the wildcard as valid input
                else:
                    # Attempt to parse the query as JSON
                    query_json = json.loads(query)  # This could return any valid JSON (string, number, etc.)

                    # Ensure the parsed query is either a JSON object (dict) or a list of JSON objects
                    if not isinstance(query_json, (dict, list)):
                        return {
                            "error": "Invalid input. Only JSON objects, arrays of objects, or wildcard '*' are allowed."}

                    # If it's a list, make sure it's a list of JSON objects
                    if isinstance(query_json, list):
                        if not all(isinstance(item, dict) for item in query_json):
                            return {"error": "Invalid input. Arrays must contain only JSON objects."}

            except json.JSONDecodeError:
                return {"error": "Invalid JSON format in query input"}

            data = {
                'group_by_rows': '',
                'agent': 'sparrow-parse',
                'keywords': '',
                'sparrow_key': key,
                'update_targets': '',
                'debug': 'false',
                'index_name': '',
                'types': '',
                'fields': query_json if query_json == "*" else json.dumps(query_json),  # Use wildcard as-is, or JSON
                'options': 'huggingface,katanaml/sparrow-qwen2-vl-7b'
            }

            # Perform the POST request
            response = requests.post(url, headers=headers, files=files, data=data)

            # Process the response and return the JSON data
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Request failed with status code {response.status_code}", "details": response.text}
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


def handle_example(example_image):
    # Find the corresponding entry in the examples array
    for example in examples:
        if example[0] == example_image:
            # Return bonds_json if Bonds table is selected
            if example_image == "bonds_table.png":
                return example_image, bonds_json, example[2]
            # Return lab_results_json if Lab results is selected
            elif example_image == "lab_results.png":
                return example_image, lab_results_json, example[2]
            # Return bank_statement_json if Bank statement is selected
            elif example_image == "bank_statement.png":
                return example_image, bank_statement_json, example[2]

    # Default return if no match found
    return None, "No example selected.", ""


# Define the UI
with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    with gr.Tab(label="Sparrow UI"):
        with gr.Row():
            with gr.Column():
                input_img = gr.Image(label="Input Document Image", type="filepath")
                query_input = gr.Textbox(label="Query", placeholder="Use * to query all data or JSON schema, e.g.: [{\"instrument_name\": \"example\"}]")
                key_input = gr.Textbox(label="Sparrow Key", type="password")
                submit_btn = gr.Button(value="Submit", variant="primary")

                # Radio button for selecting examples
                example_radio = gr.Radio(label="Select Example", choices=[ex[0] for ex in examples])

            with gr.Column():
                # JSON output for structured JSON display
                output_json = gr.JSON(label="Response (JSON)", height=900, min_height=900)


        # Function to handle example selection
        def on_example_select(selected_example):
            # Handle example selection and return the image, output (text or JSON), and query
            return handle_example(selected_example)


        # Update image, output JSON, and query when an example is selected
        example_radio.change(on_example_select,
                             inputs=example_radio,
                             outputs=[input_img, output_json, query_input])

        # When submit is clicked
        submit_btn.click(run_inference, [input_img, query_input, key_input], [output_json])

        gr.Markdown(
            """
            ---
            <p style="text-align: center;">
            Visit <a href="https://katanaml.io/" target="_blank">Katana ML</a> for more details.
            </p>
            """
        )

# Launch the app
demo.queue(api_open=False)
demo.launch(debug=True)
