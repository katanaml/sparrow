import gradio as gr
import requests
import os
from PIL import Image
import json
from datetime import datetime
import configparser
from rich import print
import geoip2.database
from pathlib import Path
from temp_cleaner import GradioTempCleaner
import mimetypes
import db_pool


# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the properties file
config.read("config.properties")

# Fetch settings
backend_url = config.get("settings", "backend_url")
version = config.get("settings", "version")

# Get model options from config with friendly names
model_options = {}  # Maps friendly name to backend options string
model_display = {}  # Maps technical name to friendly name

for key, value in config.items("settings"):
    if key.startswith("backend_options_"):
        parts = value.split(",")
        if len(parts) >= 3:
            backend_info = f"{parts[0]},{parts[1]}"
            tech_name = parts[1]
            friendly_name = parts[2]

            # Add emoji based on model characteristics
            if "Advanced" in friendly_name:
                display_name = "🦉 " + friendly_name  # Magnifying glass for high-quality models
            else:
                display_name = "🚀 " + friendly_name  # Rocket for balanced/all-purpose models

            model_options[display_name] = backend_info
            model_display[tech_name] = display_name
        else:
            # Fallback if no friendly name is provided
            backend_info = value
            tech_name = parts[1]
            friendly_name = tech_name
            display_name = "🚀 " + friendly_name  # Default emoji
            model_options[display_name] = backend_info
            model_display[tech_name] = display_name

# Set a default option if none found
if not model_options:
    default_backend = config.get("settings", "backend_options",
                                 fallback="mlx,mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit")
    tech_name = default_backend.split(",")[1]
    friendly_name = tech_name
    display_name = "🔍 " + friendly_name  # Add emoji to default
    model_options[display_name] = default_backend
    model_display[tech_name] = display_name


# GeoIP configuration
# Sign up for a free account at MaxMind: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
# Download the GeoLite2-Country database and place it in the same directory as this script
GEOIP_DB_PATH = "GeoLite2-Country.mmdb"


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Example data with placeholder JSON for lab_results and bank_statement
examples = [
    ["bonds_table.png", "Bonds table", "[{\"instrument_name\":\"str\", \"valuation\":0}]", None],
    ["lab_results.png", "Lab results", "{\"patient_name\": \"str\", \"patient_age\": \"str\", \"patient_pid\": 0, \"lab_results\": [{\"investigation\": \"str\", \"result\": 0.00, \"reference_value\": \"str\", \"unit\": \"str\"}]}", None],
    ["bank_statement.png", "Bank statement", "*", "Tables Only"]
]

# JSON data for Bonds table
bonds_json = {
    "data": [
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
    ],
    "valid": "true"
}

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
    ],
    "valid": "true"
}

bank_statement_json = {
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
    ],
}


def fetch_geolocation(ip_address):
    try:
        if not Path(GEOIP_DB_PATH).exists():
            return "Database not found"

        with geoip2.database.Reader(GEOIP_DB_PATH) as reader:
            response = reader.country(ip_address)
            return response.country.name
    except geoip2.errors.AddressNotFoundError:
        return "Unknown"
    except Exception as e:
        return f"Error: {str(e)}"


def log_request(client_ip, source="General"):
    country = fetch_geolocation(client_ip)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] Source: {source}, IP: {client_ip}, Country: {country}"
    print(log_message)


def validate_file(file_path):
    # Check file extension
    _, ext = os.path.splitext(file_path)
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']

    if ext.lower() not in allowed_extensions:
        return False

    # Double-check using mime type
    mime_type, _ = mimetypes.guess_type(file_path)
    allowed_mime_prefixes = ['image/jpeg', 'image/png', 'application/pdf']

    return any(mime_type and mime_type.startswith(prefix) for prefix in allowed_mime_prefixes)


def run_inference(file_filepath, query, key, options, crop_size, friendly_model_name, client_ip):
    if file_filepath is None:
        gr.Warning("No file provided. Please upload a file before submitting.")
        return None

    # Get the file size using the file path
    if not os.path.exists(file_filepath):
        gr.Warning("Please upload a file again and repeat inference. The file was removed after processing.")
        return None
    file_size = os.path.getsize(file_filepath)  # File size in bytes  # Get the file size in bytes
    if file_size > MAX_FILE_SIZE:
        # Clean up the temporary file
        if os.path.exists(file_filepath):
            os.remove(file_filepath)
        gr.Warning("File size exceeds 5 MB. Please upload a smaller file.")
        return None

    if not validate_file(file_filepath):
        gr.Warning("Invalid file type. Only JPG, PNG and PDF files are allowed.")
        return None

    if query is None or query.strip() == "":
        gr.Warning("No query provided. Please enter a query before submitting.")
        return None

    # Check if user provided a key and validate it
    if key is not None and key.strip() != "":
        # Verify the provided key
        if not db_pool.verify_key(key):
            gr.Warning("Invalid Sparrow Key. Please check your key or leave empty for limited usage.")
            return {
                "message": "Invalid Sparrow Key. Please obtain a valid Sparrow Key by emailing abaranovskis@redsamuraiconsulting.com."
            }

        # Key is valid, now check PDF page limit (10 pages)
        if file_filepath.lower().endswith('.pdf'):
            try:
                import pypdf
                with open(file_filepath, 'rb') as pdf_file:
                    pdf_reader = pypdf.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)

                    if num_pages > 10:
                        gr.Warning(
                            f"With a Sparrow Key, PDFs are limited to maximum 10 pages. This document has {num_pages} pages.")
                        # Clean up the temporary file
                        if os.path.exists(file_filepath):
                            os.remove(file_filepath)
                        return {
                            "message": f"PDFs are limited to maximum 10 pages even with a valid Sparrow Key. This document has {num_pages} pages. For larger documents, please contact us at abaranovskis@redsamuraiconsulting.com."
                        }
            except Exception as e:
                print(f"Error checking PDF page count: {str(e)}")
                # Continue if we can't check the page count, but log the error
    else:
        # Try to get a restricted key based on rate limiting
        key = db_pool.get_restricted_key(client_ip)

        if key is None:
            gr.Warning("Rate limit exceeded or no available keys.")
            return {
                "message": "Please obtain a Sparrow Key by emailing abaranovskis@redsamuraiconsulting.com. We offer professional consulting and implementation services for local document processing with Sparrow, tailored to your organization's needs."
            }

        # If we got here, we successfully obtained a key from the database
        # For auto-assigned keys (free tier), check PDF page limit
        if file_filepath.lower().endswith('.pdf'):
            try:
                import pypdf
                with open(file_filepath, 'rb') as pdf_file:
                    pdf_reader = pypdf.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)

                    if num_pages > 3:
                        gr.Warning(
                            f"Free tier is limited to PDFs with maximum 3 pages. This document has {num_pages} pages.")
                        # Clean up the temporary file
                        if os.path.exists(file_filepath):
                            os.remove(file_filepath)
                        return {
                            "message": f"Free tier can only process PDFs with maximum 3 pages. This document has {num_pages} pages. For larger documents, please obtain a Sparrow Key by emailing abaranovskis@redsamuraiconsulting.com."
                        }
            except Exception as e:
                print(f"Error checking PDF page count: {str(e)}")
                # Continue if we can't check the page count, but log the error

        # Display warning about limitations of using auto-assigned key
        gr.Info("Free tier: Limited to 3 calls per 6 hours, max 3-page documents.")

        # Log the auto-assignment
        country = fetch_geolocation(client_ip)
        log_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto-assigned key to IP: {client_ip}, Country: {country}"
        print(log_message)

    file_path = None
    try:
        # Extract the file extension from the uploaded file
        input_file_extension = file_filepath.split('.')[-1].lower()

        # Generate a unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"file_{timestamp}"

        # If the uploaded file is an image (e.g., jpg, jpeg, png), process it
        if input_file_extension in ['jpg', 'jpeg', 'png']:
            # Open the image
            img = Image.open(file_filepath)

            filename = f"{filename}.{input_file_extension}"
            # Save the image with the correct extension (use its original extension)
            file_path = os.path.abspath(filename)
            img.save(file_path)

            file_mime_type = f"image/{input_file_extension}"
        # If it's a PDF, just rename and keep the PDF extension
        elif input_file_extension == 'pdf':
            # Move the PDF file to the correct location without modification
            file_path = os.path.abspath(f"{filename}.pdf")
            os.rename(file_filepath, file_path)

            # Ensure the filename includes the .pdf extension
            filename = f"{filename}.pdf"
            file_mime_type = 'application/pdf'
        else:
            gr.Warning(f"Unsupported file type: {input_file_extension}. Please upload an image or PDF.")
            return None

        # Prepare the REST API call
        url = backend_url
        headers = {
            'accept': 'application/json'
        }

        # Open the file in binary mode and send it
        with open(file_path, "rb") as f:
            files = {
                'file': (filename, f, file_mime_type)
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
                        gr.Warning("Invalid input. Only JSON objects, arrays of objects, or wildcard '*' are allowed.")
                        return None

                    # If it's a list, make sure it's a list of JSON objects
                    if isinstance(query_json, list):
                        if not all(isinstance(item, dict) for item in query_json):
                            gr.Warning("Invalid input. Arrays must contain only JSON objects.")
                            return None

            except json.JSONDecodeError:
                gr.Warning("Invalid JSON format in query input")
                return None

            # Prepare the options string
            selected_options = []
            if "Tables Only" in options:
                selected_options.append("tables_only")
            if "Validation Off" in options:
                selected_options.append("validation_off")

            # Use the selected model's backend options via the friendly name
            final_options = model_options.get(friendly_model_name, model_options[friendly_names[0]])
            if selected_options:
                final_options += "," + ",".join(selected_options)

            data = {
                'query': query_json if query_json == "*" else json.dumps(query_json),  # Use wildcard as-is, or JSON
                'pipeline': 'sparrow-parse',
                'options': final_options,
                'crop_size': str(crop_size) if crop_size > 0 else '',
                'debug_dir': '',
                'debug': 'false',
                'sparrow_key': key,
                'client_ip': client_ip,
                'country': fetch_geolocation(client_ip)
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


# Initialize the temp cleaner
temp_cleaner = GradioTempCleaner(
    max_age_hours=2,             # Remove files older than 2 hours, test with 1/60 for 1 minute
    check_interval_minutes=30,   # Check every 30 minutes, test with 0.5 for 30 seconds
    remove_all=False             # Only remove files older than specified age
)


# Define the UI
with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    demo.title = "Sparrow"

    # Log initial page load
    @demo.load(api_name=False)
    def on_page_load(request: gr.Request):
        log_request(request.client.host, "Page Load")


    with gr.Tab(label="Sparrow"):
        with gr.Row():
            with gr.Column():
                input_file_comp = gr.File(
                    label="Input Document (Max 5 MB)",
                    type="filepath",
                    file_types=[".jpg", ".jpeg", ".png", ".pdf"]
                )

                image_preview_comp = gr.Image(
                    label="Image Preview",
                    type="filepath",
                    visible=False
                )
                query_input_comp = gr.Textbox(
                    label="Query",
                    placeholder="Use * to query all data or JSON schema, e.g.: [{\"instrument_name\": \"str\"}]"
                )
                options_select_comp = gr.CheckboxGroup(
                    label="Additional Options",
                    choices=["Tables Only", "Validation Off"],
                    type="value"
                )
                crop_size_comp = gr.Slider(
                    label="Crop Size",
                    value=0,
                    minimum=0,
                    maximum=600,
                    step=1,
                    info="Crop by specifying the size in pixels (0 for no cropping)"
                )

                key_input_comp = gr.Textbox(
                    label="Sparrow Key",
                    type="password",
                    placeholder="Enter your key or leave empty for limited usage"
                )

                friendly_names = list(model_options.keys())
                model_dropdown_comp = gr.Dropdown(
                    label="Vision LLM Model",
                    choices=friendly_names,
                    value=friendly_names[0] if friendly_names else "",
                    info="Select model based on your document complexity"
                )

                submit_btn = gr.Button(
                    value="Submit",
                    variant="primary"
                )

                example_radio = gr.Radio(
                    label="Select Example",
                    choices=[ex[0] for ex in examples]
                )

                key_info_message = gr.Markdown(
                    """
                    <div style="margin-top: -10px; padding: 15px; border-left: 4px solid var(--primary-500); border-radius: 6px; background-color: var(--background-fill-secondary);">
                        <div style="display: flex; align-items: flex-start;">
                            <div style="font-size: 24px; margin-right: 10px; color: var(--primary-500);">💡</div>
                            <div>
                                <p style="margin: 0; font-weight: 600; font-size: 16px; color: var(--primary-500);">Free Tier Available</p>
                                <p style="margin: 5px 0 0 0;">You can use Sparrow without entering a key for limited usage (3 calls per 6 hours, max 3-page documents).</p>
                                <p style="margin: 5px 0 0 0;">For unlimited usage, <a href="mailto:abaranovskis@redsamuraiconsulting.com" style="color: var(--primary-500); text-decoration: underline; font-weight: 500;">contact us</a> about our professional consulting and implementation services for local document processing solutions.</p>
                            </div>
                        </div>
                    </div>
                    """
                )

            with gr.Column():
                output_json = gr.JSON(
                    label="Response (JSON)",
                    height=1022,
                    min_height=1022
                )


        # Handler functions with logging
        def on_example_select(selected_example, request: gr.Request):
            log_request(request.client.host, f"Example Selection: {selected_example}")
            # Find the corresponding example data
            for example in examples:
                if example[0] == selected_example:
                    example_json = None
                    # Return appropriate JSON based on example type
                    if selected_example == "bonds_table.png":
                        example_json = bonds_json
                    elif selected_example == "lab_results.png":
                        example_json = lab_results_json
                    elif selected_example == "bank_statement.png":
                        example_json = bank_statement_json

                    # For image preview
                    preview_visible = selected_example.lower().endswith(('png', 'jpg', 'jpeg'))

                    return (
                        selected_example,  # input_file
                        example_json,  # output_json
                        gr.update(value=example[2]),  # query_input
                        gr.update(value=[example[3]] if example[3] else []),  # options_select
                        gr.update(value=0),  # crop_size
                    )

            # Default return if no match found
            return (
                None,  # input_file
                None,  # output_json
                gr.update(value=""),  # query_input
                gr.update(value=[]),  # options_select
                gr.update(value=0),  # crop_size
            )


        def update_preview(file_path, request: gr.Request):
            preview_update = None
            preview_visible = False

            if file_path:
                # Get just the file name from the path
                if hasattr(file_path, 'name'):
                    file_name = Path(file_path.name).name
                else:
                    file_name = Path(str(file_path)).name

                log_request(request.client.host, f"Preview Update: {file_name}")

                if str(file_path).lower().endswith(('png', 'jpg', 'jpeg')):
                    preview_update = file_path
                    preview_visible = True

            return (
                preview_update,  # image_preview value
                gr.update(visible=preview_visible)  # image_preview visibility
            )


        def clear_on_file_upload(file_path, request: gr.Request):
            """Separate function to handle clearing fields on file upload"""
            if file_path is None:  # Only clear when file is removed
                return (
                    gr.update(value=""),  # query_input
                    gr.update(value=[]),  # options_select
                    gr.update(value=0),  # crop_size
                    gr.update(value=None)  # example_radio
                )
            return [gr.update() for _ in range(4)]


        def run_inference_wrapper(input_file, query_input, key_input, options_select, crop_size, model_name, request: gr.Request):
            if input_file:
                # Get just the file name from the path
                if hasattr(input_file, 'name'):
                    file_name = Path(input_file.name).name
                else:
                    file_name = Path(str(input_file)).name

                log_request(request.client.host, f"Inference Request - File: {file_name}")
            else:
                log_request(request.client.host, "Inference Request - No file")

            return run_inference(input_file, query_input, key_input, options_select, crop_size, model_name, request.client.host)


        # Connect components with updated handlers
        example_radio.change(
            on_example_select,
            inputs=[example_radio],
            outputs=[
                input_file_comp,
                output_json,
                query_input_comp,
                options_select_comp,
                crop_size_comp
            ],
            api_name=False
        )

        # Split the file upload handling into two events
        input_file_comp.change(
            update_preview,
            inputs=[input_file_comp],
            outputs=[
                image_preview_comp,
                image_preview_comp
            ],
            api_name=False
        )

        input_file_comp.change(
            clear_on_file_upload,
            inputs=[input_file_comp],
            outputs=[
                query_input_comp,
                options_select_comp,
                crop_size_comp,
                example_radio
            ],
            api_name=False
        )

        submit_btn.click(
            run_inference_wrapper,
            inputs=[
                input_file_comp,
                query_input_comp,
                key_input_comp,
                options_select_comp,
                crop_size_comp,
                model_dropdown_comp
            ],
            outputs=[output_json],
            api_name=False
        )

        gr.Markdown(
            f"""
            ---
            <p style="text-align: center;">
            Visit <a href="https://katanaml.io/" target="_blank">Katana ML</a> and <a href="https://github.com/katanaml/sparrow" target="_blank">Sparrow</a> GitHub for more details.
            </p>
            <p style="text-align: center;">
            <strong>Version:</strong> {version}
            </p>
            """
        )


# Launch the app
if __name__ == "__main__":
    # Initialize the DB connection pool (no-op if DB is disabled)
    db_pool.initialize_connection_pool()

    # Start the temp cleaner
    temp_cleaner.start()

    try:
        demo.queue(api_open=False, max_size=10)
        demo.launch(server_name="0.0.0.0", server_port=7861, debug=False, pwa=True, show_api=False)
    finally:
        # Make sure to stop the cleaner when the app exits
        temp_cleaner.stop()

        # Close the DB connection pool (the atexit handler will be a no-op if already closed)
        db_pool.close_connection_pool()