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
import dashboard
import feedback
import shutil


# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the properties file
config.read("config.properties")

# Fetch settings
backend_url = config.get("settings", "backend_url")
version = config.get("settings", "version")
protected_access = config.getboolean("settings", "protected_access", fallback=True)

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
                                 fallback="mlx,mlx-community/Ministral-3-14B-Instruct-2512-8bit")
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
    ["bank_statement.png", "Bank statement", "*", "Table Extraction"]
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


def run_inference(file_filepath, query, key, table_extraction, validation_off, friendly_model_name, client_ip):
    if file_filepath is None:
        gr.Warning("No file provided. Please upload a file before submitting.")
        return None, None

    # Get the file size using the file path
    if not os.path.exists(file_filepath):
        gr.Warning("Please upload a file again and repeat inference. The file was removed after processing.")
        return None, None
    file_size = os.path.getsize(file_filepath)  # File size in bytes  # Get the file size in bytes
    if file_size > MAX_FILE_SIZE:
        # Clean up the temporary file
        if os.path.exists(file_filepath):
            os.remove(file_filepath)
        gr.Warning("File size exceeds 5 MB. Please upload a smaller file.")
        return None, None

    if not validate_file(file_filepath):
        gr.Warning("Invalid file type. Only JPG, PNG and PDF files are allowed.")
        return None, None

    if query is None or query.strip() == "":
        gr.Warning("No query provided. Please enter a query before submitting.")
        return None, None

    # Check if user provided a key and validate it
    if protected_access:
        if key is not None and key.strip() != "":
            # Verify the provided key
            if not db_pool.verify_key(key):
                gr.Warning("Invalid Sparrow Key. Please check your key or leave empty for limited usage.")
                return {
                    "message": "Invalid Sparrow Key. Please obtain a valid Sparrow Key by emailing abaranovskis@redsamuraiconsulting.com."
                }, None

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
                            }, None
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
                }, None

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
                            }, None
                except Exception as e:
                    print(f"Error checking PDF page count: {str(e)}")
                    # Continue if we can't check the page count, but log the error

            # Display warning about limitations of using auto-assigned key
            gr.Info("Free tier: Limited to 30 calls per 6 hours, max 3-page documents.")

            # Log the auto-assignment
            country = fetch_geolocation(client_ip)
            log_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto-assigned key to IP: {client_ip}, Country: {country}"
            print(log_message)
    else:
        # Protected access is disabled - skip all key validation
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Protected access disabled - skipping key validation for IP: {client_ip}")

        # Use a default key or the provided key without validation
        if key is None or key.strip() == "":
            key = "unrestricted_access"  # Default key when protected access is disabled

        # Optionally show an info message to user
        gr.Info("Protected access disabled - unlimited usage available.")

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
            # Copy the PDF file to the correct location without modification
            file_path = os.path.abspath(f"{filename}.pdf")
            shutil.copy2(file_filepath, file_path)  # Use copy2 to preserve metadata

            # Ensure the filename includes the .pdf extension
            filename = f"{filename}.pdf"
            file_mime_type = 'application/pdf'
        else:
            gr.Warning(f"Unsupported file type: {input_file_extension}. Please upload an image or PDF.")
            return None, None

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
                        return None, None

                    # If it's a list, make sure it's a list of JSON objects
                    if isinstance(query_json, list):
                        if not all(isinstance(item, dict) for item in query_json):
                            gr.Warning("Invalid input. Arrays must contain only JSON objects.")
                            return None, None

            except json.JSONDecodeError:
                gr.Warning("Invalid JSON format in query input")
                return None, None

            # Prepare the options string
            selected_options = []
            if table_extraction:
                selected_options.append("tables_only")
            if validation_off:
                selected_options.append("validation_off")

            # Use the selected model's backend options via the friendly name
            final_options = model_options.get(friendly_model_name, model_options[friendly_names[0]])
            if selected_options:
                final_options += "," + ",".join(selected_options)

            data = {
                'query': query_json if query_json == "*" else json.dumps(query_json),  # Use wildcard as-is, or JSON
                'pipeline': 'sparrow-parse',
                'options': final_options,
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
                gr.Info("Inference completed successfully! We'd greatly appreciate your feedback.")
                return response.json(), key
            else:
                return {"error": f"Request failed with status code {response.status_code}", "details": response.text}, None
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)


def summarize_result(json_data, key, client_ip, model_name):
    """
    Makes a REST call to the instruction-inference endpoint to summarize JSON data.

    Args:
        json_data: The JSON data to summarize
        key: Sparrow key for API authentication
        client_ip: Client IP address
        model_name: Model name selected for inference

    Returns:
        str: Markdown-formatted summarize from the LLM
    """
    try:
        # Format the instruction and payload for the LLM
        json_str = json.dumps(json_data, indent=2) if not isinstance(json_data, str) else json_data
        query = f"instruction: summarize this json data, payload: {json_str}"

        # Get model options from the same source as run_inference
        # Use the selected model's backend options via the friendly name
        final_options = model_options.get(model_name, model_options[friendly_names[0]])

        # Prepare the form data for the POST request exactly like in run_inference
        data = {
            'query': query,
            'pipeline': 'sparrow-instructor',
            'options': final_options,
            'debug_dir': '',
            'debug': 'false',
            'sparrow_key': key,
            'client_ip': client_ip,
            'country': fetch_geolocation(client_ip)
        }

        # Make the API call
        instruction_url = config.get("settings", "backend_url").replace("/inference", "/instruction-inference")

        # Perform the POST request
        response = requests.post(
            instruction_url,
            headers={'accept': 'application/json'},
            data=data
        )

        # Process the response
        if response.status_code == 200:
            result = response.json() if response.content else "No summary generated."

            # If the result is a string, return it directly
            if isinstance(result, str):
                return result

            # Otherwise, return the result (which might be JSON or text)
            return result
        else:
            return f"Error: Failed to generate summary. Status code: {response.status_code}\n\nDetails: {response.text}"

    except Exception as e:
        return f"Error generating summary: {str(e)}"


# Initialize the temp cleaner
temp_cleaner = GradioTempCleaner(
    max_age_hours=2,             # Remove files older than 2 hours, test with 1/60 for 1 minute
    check_interval_minutes=30,   # Check every 30 minutes, test with 0.5 for 30 seconds
    remove_all=False             # Only remove files older than specified age
)


# CSS to hide default Gradio navigation and style our custom navigation
custom_css = """
/* Page background — subtle warm grey so white component cards stand out gently */
.gradio-container {
    background: #f8f7f5 !important;
    min-height: 100vh;
    max-width: none !important;
}

/* Dark mode page background */
@media (prefers-color-scheme: dark) {
    .gradio-container {
        background: #1a1a1a !important;
    }
}

.dark .gradio-container,
[data-theme="dark"] .gradio-container {
    background: #1a1a1a !important;
}

/* Trim the top whitespace left over where Gradio 6's navbar used to sit, and widen the content */
.gradio-container > main,
.gradio-container .contain {
    padding: 0 !important;
    max-width: none !important;
}

/* Flat block borders with light divider line — uniform, no card-like shadow */
.block,
.gr-form, .gr-box {
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    box-shadow: none !important;
}

@media (prefers-color-scheme: dark) {
    .block,
    .gr-form, .gr-box {
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
    }
}

.dark .block, .dark .gr-form, .dark .gr-box,
[data-theme="dark"] .block,
[data-theme="dark"] .gr-form,
[data-theme="dark"] .gr-box {
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

/* Full border opt-out (e.g. footer markdown that stands alone) */
.block.no-border,
.no-border.block,
.no-border {
    border: none !important;
    box-shadow: none !important;
}

/* Remove only top/bottom borders — keeps left/right so stacked blocks form a continuous outer rectangle */
.block.merge-edges,
.merge-edges.block,
.merge-edges {
    border-top: none !important;
    border-bottom: none !important;
    box-shadow: none !important;
}

/* Drop the touching border edges of neighbors, so merged blocks blend in seamlessly */
.merge-edges + .block {
    border-top: none !important;
}
.block:has(+ .merge-edges) {
    border-bottom: none !important;
}

/* Lighter border for opted-in components (e.g. feedback form fields) */
.block.small-border,
.small-border.block,
.small-border {
    border: 1px solid rgba(0, 0, 0, 0.04) !important;
}

/* Footer feature cards — dark mode aware */
.feature-card {
    background: white;
    border-radius: 12px;
    border: 1px solid rgba(44, 82, 130, 0.15);
    padding: 1rem 1.25rem;
}
.feature-card .feature-title {
    font-size: 14px;
    font-weight: 600;
    color: #2c5282;
    margin: 0 0 8px 0;
}
.feature-card .feature-body {
    font-size: 13px;
    color: #4a5568;
    line-height: 1.6;
    margin: 0;
}

@media (prefers-color-scheme: dark) {
    .feature-card {
        background: rgba(255, 255, 255, 0.04);
        border-color: rgba(255, 255, 255, 0.12);
    }
    .feature-card .feature-title {
        color: #7aa8d8;
    }
    .feature-card .feature-body {
        color: #c8cdd4;
    }
}

.dark .feature-card,
[data-theme="dark"] .feature-card {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.12);
}
.dark .feature-card .feature-title,
[data-theme="dark"] .feature-card .feature-title {
    color: #7aa8d8;
}
.dark .feature-card .feature-body,
[data-theme="dark"] .feature-card .feature-body {
    color: #c8cdd4;
}

/* Hide Gradio's auto-generated navbar (gr.Navbar visible=False is broken in 6.x — gradio-app/gradio#12174) */
.nav-holder,
nav.fillable {
    display: none !important;
}

/* Remove all margins and padding from navigation elements */
.navigation-header {
    margin: 0 !important;
    padding: 0 !important;
    margin-bottom: 0 !important;
}

.navigation-header .gr-prose {
    margin: 0 !important;
    padding: 0 !important;
}

.custom-navigation {
    margin: 0 !important;
    margin-bottom: 0 !important;
}

/* Remove extra spacing between consecutive HTML blocks */
.gr-html + .gr-html {
    margin-top: -10px !important;
}

/* Alternative approach - target the HTML component wrapper */
div[data-testid="HTML"] + div[data-testid="HTML"] {
    margin-top: -15px !important;
}

/* Enhanced styling for selected navigation items */
.nav-selected {
    background: rgba(255,255,255,0.4) !important;
    border: 2px solid rgba(255,255,255,0.6) !important;
    font-weight: 600 !important;
}

.nav-selected:hover {
    background: rgba(255,255,255,0.5) !important;
}

/* Responsive navigation - hide text labels on narrow screens */
@media screen and (max-width: 768px) {
    .nav-text {
        display: none !important;
    }

    .custom-navigation nav {
        gap: 10px !important;
    }

    .custom-navigation nav a {
        padding: 8px 12px !important;
        min-width: 44px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* Enhanced selected item visibility on mobile */
    .nav-selected {
        background: rgba(255,255,255,0.5) !important;
        border: 2px solid rgba(255,255,255,0.7) !important;
    }
}

/* Mobile responsive navigation - hide text on narrow screens */
@media (max-width: 768px) {
    /* Hide navigation text spans on mobile */
    .nav-text {
        display: none !important;
    }

    /* Adjust navigation gap for mobile */
    .mobile-nav {
        gap: 10px !important;
    }

    /* Adjust navigation link padding for mobile */
    .nav-link {
        padding: 8px 12px !important;
        min-width: 44px !important;
        text-align: center !important;
    }

    /* Make title more compact on mobile */
    .nav-title {
        font-size: 20px !important;
    }
}

/* Disabled state for Vision LLM Model dropdown */
#model_dropdown.disabled,
#model_dropdown:has(input:disabled) {
    opacity: 0.45 !important;
    pointer-events: none !important;
}

/* For very narrow screens (phones in portrait) */
@media (max-width: 480px) {
    .mobile-nav {
        gap: 8px !important;
    }

    .nav-link {
        padding: 6px 10px !important;
        min-width: 40px !important;
    }

    .nav-title {
        font-size: 18px !important;
    }
}


"""


result_summary_placeholder = """
<div style="margin-top: -10px; padding: 15px; border-left: 4px solid var(--primary-500); border-radius: 6px; background-color: var(--background-fill-secondary);">
    <div style="display: flex; align-items: flex-start;">
        <div style="font-size: 24px; margin-right: 10px; color: var(--primary-500);">🔍</div>
        <div>
            <p style="margin: 0; font-weight: 600; font-size: 16px; color: var(--primary-500);">Summarize Your Results</p>
            <p style="margin: 5px 0 0 0;">• After extracting data from your document, you'll be able to summarize the JSON results in plain language.</p>
            <p style="margin: 5px 0 0 0;">• The 'Summarize this result' button will appear only after inference completes successfully.</p>
            <p style="margin: 5px 0 0 0;">• This feature helps transform technical JSON structures into meaningful insights about your document content.</p>
        </div>
    </div>
</div>
"""


# Define the Home page
with gr.Blocks() as demo:
    demo.title = "Sparrow"

    # Add navigation using Markdown with HTML content for better integration
    with gr.Row():
        gr.Markdown(
            """
            <div class="custom-navigation" style="background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%); border-radius: 10px;">
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 15px 20px;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 24px; margin-right: 10px;">🚀</span>
                        <h1 class="nav-title" style="margin: 0; color: white; font-size: 24px; font-weight: 600;">Sparrow</h1>
                    </div>
                    <nav class="mobile-nav" style="display: flex; gap: 20px;">
                        <a href="/" class="nav-link nav-selected" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.4); font-weight: 600; transition: all 0.3s ease; border: 2px solid rgba(255,255,255,0.6);" 
                           onmouseover="this.style.background='rgba(255,255,255,0.5)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.4)'; this.style.color='white';">🚀<span class="nav-text" style="color: white;"> Process</span></a>
                        <a href="/dashboard" class="nav-link" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.1); font-weight: 500; transition: all 0.3s ease;" 
                           onmouseover="this.style.background='rgba(255,255,255,0.2)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.1)'; this.style.color='white';">📊<span class="nav-text" style="color: white;"> Dashboard</span></a>
                        <a href="/feedback" class="nav-link" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.1); font-weight: 500; transition: all 0.3s ease;" 
                           onmouseover="this.style.background='rgba(255,255,255,0.2)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.1)'; this.style.color='white';">💬<span class="nav-text" style="color: white;"> Feedback</span></a>
                    </nav>
                </div>
                <div style="padding: 0 20px 15px; border-top: 1px solid rgba(255,255,255,0.2);">
                    <div style="padding-top: 12px;">
                        <p style="margin: 0; font-weight: 600; font-size: 16px; color: white; opacity: 0.95;">Document Processing Platform</p>
                    </div>
                </div>
            </div>
            """,
            elem_classes=["navigation-header"]
        )

    # Log initial page load
    @demo.load(api_name=False)
    def on_page_load(request: gr.Request):
        log_request(request.client.host, "Page Load")

    with gr.Row():
        with gr.Column():
            input_file_comp = gr.File(
                label="Input Document (Max 5 MB, removed after inference)",
                type="filepath",
                file_types=[".jpg", ".jpeg", ".png", ".pdf"]
            )

            image_preview_comp = gr.Image(
                label="Image Preview",
                type="filepath",
                visible=False,
                buttons=["download", "fullscreen"]
            )

            query_input_comp = gr.Textbox(
                label="Query",
                placeholder="Use * to query all data or JSON schema, e.g.: [{\"instrument_name\": \"str\"}]",
                lines=3
            )

            with gr.Group(elem_classes=["table-extraction-group"]):
                table_extraction_comp = gr.Checkbox(
                    label="Table Extraction",
                    value=False,
                    info="Focus extraction on table content only. Ideal for documents where data is organized in rows and columns — financial reports, lab results, portfolio statements."
                )

            validation_off_comp = gr.Checkbox(
                label="Validation Off",
                value=False,
                info="Disable automatic validation of extracted results."
            )

            key_input_comp = gr.Textbox(
                label="Sparrow Key",
                type="password",
                placeholder="Enter your Sparrow Key for extended access and additional functionality",
                visible=protected_access,
                elem_classes=["merge-edges"]
            )

            friendly_names = list(model_options.keys())
            model_dropdown_comp = gr.Dropdown(
                label="Vision LLM Model",
                choices=friendly_names,
                value=friendly_names[0] if friendly_names else "",
                info="Select model based on your document complexity",
                elem_id="model_dropdown"
            )

            submit_btn = gr.Button(
                value="Submit",
                variant="primary"
            )

            example_radio = gr.Radio(
                label="Select Example",
                choices=[ex[0] for ex in examples],
                value="bonds_table.png"  # Set bonds_table.png as default
            )

            if protected_access:
                key_info_message = gr.Markdown(
                    """
                    <div style="margin-top: -10px; padding: 15px; border-left: 4px solid var(--primary-500); border-radius: 6px; background-color: var(--background-fill-secondary);">
                        <div style="display: flex; align-items: flex-start;">
                            <div style="font-size: 24px; margin-right: 10px; color: var(--primary-500);">💡</div>
                            <div>
                                <p style="margin: 0; font-weight: 600; font-size: 16px; color: var(--primary-500);">Free Tier Available</p>
                                <p style="margin: 5px 0 0 0;">• You can use Sparrow without entering a key for limited usage (30 calls per 6 hours, max 3-page documents).</p>
                                <p style="margin: 5px 0 0 0;">• For unlimited usage, <a href="mailto:abaranovskis@redsamuraiconsulting.com" style="color: var(--primary-500); text-decoration: underline; font-weight: 500;">contact us</a> about our professional consulting and implementation services for local document processing solutions.</p>
                            </div>
                        </div>
                    </div>
                    """,
                    elem_classes=["merge-edges"]
                )
            else:
                key_info_message = gr.Markdown(
                    """
                    <div style="margin-top: -10px; padding: 15px; border-left: 4px solid var(--success-500); border-radius: 6px; background-color: var(--success-50);">
                        <div style="display: flex; align-items: flex-start;">
                            <div style="font-size: 24px; margin-right: 10px; color: var(--success-500);">🔓</div>
                            <div>
                                <p style="margin: 0; font-weight: 600; font-size: 16px; color: var(--success-500);">Unrestricted Access</p>
                                <p style="margin: 5px 0 0 0;">• Protected access is disabled - unlimited document processing available.</p>
                                <p style="margin: 5px 0 0 0;">• No Sparrow Key required for this deployment.</p>
                            </div>
                        </div>
                    </div>
                    """,
                    elem_classes=["merge-edges"]
                )

        with gr.Column():
            # Regular JSON output (initially visible)
            output_json = gr.JSON(
                label="Response (JSON)",
                height=1022,
                min_height=1022,
                visible=True
            )

            summarize_btn = gr.Button(
                value="Summarize this result",
                variant="secondary",
                visible=False
            )

            # Add hidden state to store the actual key used
            active_key_state = gr.State(value=None)

            summarize_text = gr.Markdown(
                value=result_summary_placeholder
            )


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

                is_table_extraction = example[3] == "Table Extraction"
                return (
                    selected_example,  # input_file_comp
                    gr.update(value=example[2]),  # query_input_comp
                    gr.update(value=is_table_extraction),  # table_extraction_comp
                    gr.update(value=False),  # validation_off_comp
                    gr.update(visible=True, value=example_json),  # output_json
                    gr.update(visible=False),  # summarize_btn
                    gr.update(value=result_summary_placeholder),  # summarize_text
                    gr.update(interactive=not is_table_extraction),  # model_dropdown_comp
                )

        # Default return if no match found
        return (
            None,  # input_file_comp
            gr.update(value=""),  # query_input_comp
            gr.update(value=False),  # table_extraction_comp
            gr.update(value=False),  # validation_off_comp
            gr.update(visible=True, value=None),  # output_json
            gr.update(visible=False),  # summarize_btn
            gr.update(value=result_summary_placeholder),  # summarize_text
            gr.update(interactive=True),  # model_dropdown_comp
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


    example_filenames = {ex[0] for ex in examples}

    def clear_on_file_upload(file_path, request: gr.Request):
        """Separate function to handle clearing fields on file upload"""
        if file_path is None:  # Only clear when file is removed
            return (
                gr.update(value=""),  # query_input
                gr.update(value=False),  # table_extraction_comp
                gr.update(value=False),  # validation_off_comp
                gr.update(value=None),  # example_radio
                gr.update(visible=True, value=None),  # Show empty regular JSON
                gr.update(visible=False),  # Hide summarize button
                gr.update(value=result_summary_placeholder),  # Reset summary text
                gr.update(interactive=True),  # model_dropdown_comp (re-enable)
            )
        else:
            # When an example file is loaded programmatically, leave query unchanged
            is_example = Path(str(file_path)).name in example_filenames
            return (
                gr.update() if is_example else gr.update(value="*"),  # query_input
                gr.update(),  # table_extraction_comp (unchanged)
                gr.update(),  # validation_off_comp (unchanged)
                gr.update(),  # example_radio (unchanged)
                gr.update(visible=True),  # Show regular JSON output
                gr.update(visible=False),  # Hide summarize button
                gr.update(value=result_summary_placeholder),  # Reset summary text
                gr.update(),  # model_dropdown_comp (unchanged)
            )


    def run_inference_wrapper(input_file, query_input, key_input, table_extraction, validation_off, model_name,
                              request: gr.Request):
        if input_file:
            # Get just the file name from the path
            if hasattr(input_file, 'name'):
                file_name = Path(input_file.name).name
            else:
                file_name = Path(str(input_file)).name

            log_request(request.client.host, f"Inference Request - File: {file_name}")
        else:
            log_request(request.client.host, "Inference Request - No file")

        # Get inference result
        result, actual_key = run_inference(input_file, query_input, key_input, table_extraction, validation_off,
                                           model_name, request.client.host)

        summarize_visible = actual_key is not None

        return (
            gr.update(visible=True, value=result),  # Show and update regular JSON output
            gr.update(visible=summarize_visible, interactive=True),  # Update summarize button
            actual_key,  # Store the key
        )


    def summarize_result_wrapper(regular_json, key_input, model_dropdown_comp, request: gr.Request):
        """Wrapper function that calls the standalone summarize_result function"""
        log_request(request.client.host, "LLM instruction request")

        summarize = summarize_result(
            regular_json,
            key_input,
            request.client.host,
            model_dropdown_comp
        )

        return gr.update(interactive=False), summarize


    # Connect components with updated handlers
    example_radio.change(
        on_example_select,
        inputs=[example_radio],
        outputs=[
            input_file_comp,
            query_input_comp,
            table_extraction_comp,
            validation_off_comp,
            output_json,
            summarize_btn,
            summarize_text,
            model_dropdown_comp,
        ],
        api_name=False
    )

    table_extraction_comp.change(
        lambda val: gr.update(interactive=not val),
        inputs=[table_extraction_comp],
        outputs=[model_dropdown_comp],
        api_name=False
    )

    # Initialize with default example data on page load
    def initialize_default_example():
        """Initialize the page with bonds_table.png example data"""
        selected_example = "bonds_table.png"

        # Find the corresponding example data
        for example in examples:
            if example[0] == selected_example:
                example_json = bonds_json  # Use bonds_json for bonds_table.png
                is_table_extraction = example[3] == "Table Extraction"

                return (
                    selected_example,  # input_file_comp
                    gr.update(value=example[2]),  # query_input_comp
                    gr.update(value=is_table_extraction),  # table_extraction_comp
                    gr.update(value=False),  # validation_off_comp
                    gr.update(visible=True, value=example_json),  # output_json
                    gr.update(visible=False),  # summarize_btn
                    gr.update(value=result_summary_placeholder),  # summarize_text
                    gr.update(interactive=not is_table_extraction),  # model_dropdown_comp
                )

        # Default return if no match found (shouldn't happen)
        return (None, "", False, False, None, gr.update(visible=False), result_summary_placeholder, gr.update(interactive=True))

    # Trigger default example selection on page load
    demo.load(
        fn=initialize_default_example,
        outputs=[
            input_file_comp,
            query_input_comp,
            table_extraction_comp,
            validation_off_comp,
            output_json,
            summarize_btn,
            summarize_text,
            model_dropdown_comp,
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
            table_extraction_comp,
            validation_off_comp,
            example_radio,
            output_json,
            summarize_btn,
            summarize_text,
            model_dropdown_comp,
        ],
        api_name=False
    )

    submit_btn.click(
        run_inference_wrapper,
        inputs=[
            input_file_comp,
            query_input_comp,
            key_input_comp,
            table_extraction_comp,
            validation_off_comp,
            model_dropdown_comp
        ],
        outputs=[
            output_json,
            summarize_btn,
            active_key_state,
        ],
        api_name=False
    )

    summarize_btn.click(
        summarize_result_wrapper,
        inputs=[
            output_json,
            active_key_state,
            model_dropdown_comp
        ],
        outputs=[summarize_btn, summarize_text],
        api_name=False
    )

    gr.Markdown(
        f"""
        ---
        <div style="padding: 0 0 1rem 0;">
            <p style="text-align: center; font-size: 15px; font-weight: 600; color: #2c5282; margin: 0 0 1rem 0;">Data processing with ML, LLM and Vision LLM</p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px;">
                <div class="feature-card">
                    <p class="feature-title">🔍 Document Extraction</p>
                    <p class="feature-body">Extracts structured data from invoices, receipts, bank statements, and tables using on-device Vision LLM models. Supports multi-page PDF, page classification, table processing with Sparrow Templates, bounding box annotation, and schema validation. No cloud dependencies.</p>
                </div>
                <div class="feature-card">
                    <p class="feature-title">📋 Business Rules</p>
                    <p class="feature-body">Define business logic directly at the LLM level — formatting rules, derived fields, classification, and data transformation without post-processing code. Query schemas support field types and optional fields, giving full control over extraction structure and output format.</p>
                </div>
                <div class="feature-card">
                    <p class="feature-title">🤖 Sparrow Agent</p>
                    <p class="feature-body">Supports two inference modes — Vision LLM for document data extraction and Text LLM for instruction-based processing, enabling arithmetic, validation, and decision making as standalone workflow steps. Orchestrates complex pipelines chaining classification, extraction, and field validation with visual monitoring and error handling.</p>
                </div>
            </div>
            <div style="text-align: center; margin-top: 1rem;">
                <span style="font-size: 13px; color: #6b7280;">
                    Visit <a href="https://katanaml.io/" target="_blank" style="color: #2c5282; text-decoration: none; font-weight: 600;">Katana ML</a> • <a href="https://github.com/katanaml/sparrow" target="_blank" style="color: #2c5282; text-decoration: none; font-weight: 600;">Sparrow</a> GitHub &nbsp; Version {version}
                </span>
            </div>
        </div>
        """,
        elem_classes=["no-border"]
    )

# Dashboard page
with demo.route("Dashboard", "/dashboard"):
    # Add navigation using Markdown with HTML content for better integration
    with gr.Row():
        gr.Markdown(
            """
            <div class="custom-navigation" style="background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%); border-radius: 10px;">
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 15px 20px;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 24px; margin-right: 10px;">🚀</span>
                        <h1 style="margin: 0; color: white; font-size: 24px; font-weight: 600;">Sparrow</h1>
                    </div>
                    <nav style="display: flex; gap: 20px;">
                        <a href="/" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.1); font-weight: 500; transition: all 0.3s ease;" 
                           onmouseover="this.style.background='rgba(255,255,255,0.2)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.1)'; this.style.color='white';">🚀<span class="nav-text" style="color: white;"> Process</span></a>
                        <a href="/dashboard" class="nav-selected" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.4); font-weight: 600; transition: all 0.3s ease; border: 2px solid rgba(255,255,255,0.6);" 
                           onmouseover="this.style.background='rgba(255,255,255,0.5)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.4)'; this.style.color='white';">📊<span class="nav-text" style="color: white;"> Dashboard</span></a>
                        <a href="/feedback" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.1); font-weight: 500; transition: all 0.3s ease;" 
                           onmouseover="this.style.background='rgba(255,255,255,0.2)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.1)'; this.style.color='white';">💬<span class="nav-text" style="color: white;"> Feedback</span></a>
                    </nav>
                </div>
                <div style="padding: 0 20px 15px; border-top: 1px solid rgba(255,255,255,0.2);">
                    <div style="padding-top: 12px;">
                        <p style="margin: 0; font-weight: 600; font-size: 16px; color: white; opacity: 0.95;">Analytics & Metrics</p>
                    </div>
                </div>
            </div>
            """,
            elem_classes=["navigation-header"]
        )
    try:
        dashboard.demo.render()
    except gr.exceptions.DuplicateBlockError:
        # Block already rendered, skip during hot reload
        pass


# Feedback page
with demo.route("Feedback", "/feedback"):
    # Add navigation using Markdown with HTML content for better integration
    with gr.Row():
        gr.Markdown(
            """
            <div class="custom-navigation" style="background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%); border-radius: 10px;">
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 15px 20px;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 24px; margin-right: 10px;">🚀</span>
                        <h1 style="margin: 0; color: white; font-size: 24px; font-weight: 600;">Sparrow</h1>
                    </div>
                    <nav style="display: flex; gap: 20px;">
                        <a href="/" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.1); font-weight: 500; transition: all 0.3s ease;" 
                           onmouseover="this.style.background='rgba(255,255,255,0.2)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.1)'; this.style.color='white';">🚀<span class="nav-text" style="color: white;"> Process</span></a>
                        <a href="/dashboard" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.1); font-weight: 500; transition: all 0.3s ease;" 
                           onmouseover="this.style.background='rgba(255,255,255,0.2)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.1)'; this.style.color='white';">📊<span class="nav-text" style="color: white;"> Dashboard</span></a>
                        <a href="/feedback" class="nav-selected" style="color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; background: rgba(255,255,255,0.4); font-weight: 600; transition: all 0.3s ease; border: 2px solid rgba(255,255,255,0.6);" 
                           onmouseover="this.style.background='rgba(255,255,255,0.5)'; this.style.color='white';" 
                           onmouseout="this.style.background='rgba(255,255,255,0.4)'; this.style.color='white';">💬<span class="nav-text" style="color: white;"> Feedback</span></a>
                    </nav>
                </div>
                <div style="padding: 0 20px 15px; border-top: 1px solid rgba(255,255,255,0.2);">
                    <div style="padding-top: 12px;">
                        <p style="margin: 0; font-weight: 600; font-size: 16px; color: white; opacity: 0.95;">User Feedback</p>
                    </div>
                </div>
            </div>
            """,
            elem_classes=["navigation-header"]
        )
    try:
        feedback.demo.render()
    except gr.exceptions.DuplicateBlockError:
        # Block already rendered, skip during hot reload
        pass


# Launch the app
if __name__ == "__main__":
    # Initialize the DB connection pool (no-op if DB is disabled)
    db_pool.initialize_connection_pool()

    # Start the temp cleaner
    temp_cleaner.start()

    try:
        demo.queue(api_open=False, max_size=10)
        demo.launch(server_name="0.0.0.0", server_port=7861, debug=False, pwa=True, footer_links=[], share=False, favicon_path="favicon.ico", theme=gr.themes.Ocean(), css=custom_css)
    finally:
        # Make sure to stop the cleaner when the app exits
        temp_cleaner.stop()

        # Close the DB connection pool (the atexit handler will be a no-op if already closed)
        db_pool.close_connection_pool()