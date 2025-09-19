import gradio as gr
import db_pool
from datetime import datetime
from rich import print
import geoip2.database
from pathlib import Path
import configparser

# Create a ConfigParser object and read settings
config = configparser.ConfigParser()
config.read("config.properties")

# Fetch version
version = config.get("settings", "version")

# GeoIP configuration - reusing the same pattern from app.py
GEOIP_DB_PATH = "GeoLite2-Country.mmdb"


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


def log_request(client_ip, source="Feedback"):
    country = fetch_geolocation(client_ip)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] Source: {source}, IP: {client_ip}, Country: {country}"
    print(log_message)


# Define the feedback form interface
with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    demo.title = "Sparrow Feedback"


    # Log page load
    @demo.load(api_name=False)
    def on_page_load(request: gr.Request):
        log_request(request.client.host, "Feedback Page Load")

    # Form components
    with gr.Group():
        email_input = gr.Textbox(
            label="Email Address",
            placeholder="your.email@example.com",
            info="We'll use this to follow up if needed"
        )

        feedback_text = gr.TextArea(
            label="Your Feedback",
            placeholder="Tell us what you think about Sparrow...",
            info="Maximum 1000 characters",
            max_lines=10
        )

        submit_button = gr.Button("Submit Feedback", variant="primary")


    # Define the submission handler
    def submit_feedback(email, feedback, request: gr.Request):
        # Log the submission attempt
        log_request(request.client.host, "Feedback Submission")

        # Basic validation
        if not email or not '@' in email:
            gr.Warning("Please enter a valid email address.")
            return email, feedback  # Return current values to preserve them

        if not feedback:
            gr.Warning("Please enter your feedback.")
            return email, feedback  # Return current values to preserve them

        # Check feedback length
        if len(feedback) > 1000:
            gr.Warning("Feedback must be less than 1000 characters. Please shorten your message.")
            return email, feedback  # Return current values to preserve them

        # Try to save to database
        success = db_pool.save_user_feedback(email, feedback)

        if success:
            # Clear the form on success
            gr.Info("Thank you for your feedback! We appreciate your input.")
            return "", ""  # Clear both fields
        else:
            gr.Warning("There was an error submitting your feedback. Please try again later.")
            return email, feedback  # Keep current values


    # Connect the submit button to the handler
    submit_button.click(
        submit_feedback,
        inputs=[email_input, feedback_text],
        outputs=[email_input, feedback_text],
        api_name=False
    )

    # Footer with version information - matches other pages
    with gr.Row():
        gr.Markdown(
            f"""
            ---
            <div style="text-align: center; margin: 25px 0 15px 0; padding: 22px 18px; background: linear-gradient(135deg, rgba(44, 82, 130, 0.08) 0%, rgba(44, 82, 130, 0.12) 100%); border-radius: 10px; border-top: 3px solid var(--primary-500); box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04); border: 1px solid rgba(44, 82, 130, 0.15);">
                <h3 style="margin: 0 0 10px 0; font-weight: 700; font-size: 20px; color: #2c5282; letter-spacing: -0.3px;">Data processing with ML, LLM and Vision LLM</h3>
                <p style="margin: 8px 0 16px 0; color: #4a5568; font-size: 14px; line-height: 1.5; max-width: 600px; margin-left: auto; margin-right: auto;">Sparrow extracts structured data from documents, forms, and images with high accuracy. Process invoices, receipts, bank statements, and tables using on-device Vision LLM models.</p>
                <div style="display: flex; justify-content: center; align-items: center; gap: 15px; flex-wrap: wrap; margin-top: 12px;">
                    <span style="font-size: 14px; color: #374151;">
                        Visit <a href="https://katanaml.io/" target="_blank" style="color: #2c5282; text-decoration: none; font-weight: 600; border-bottom: 1px solid transparent; transition: all 0.2s ease;" onmouseover="this.style.borderBottom='1px solid #2c5282'; this.style.color='#1a365d'" onmouseout="this.style.borderBottom='1px solid transparent'; this.style.color='#2c5282'">Katana ML</a> • <a href="https://github.com/katanaml/sparrow" target="_blank" style="color: #2c5282; text-decoration: none; font-weight: 600; border-bottom: 1px solid transparent; transition: all 0.2s ease;" onmouseover="this.style.borderBottom='1px solid #2c5282'; this.style.color='#1a365d'" onmouseout="this.style.borderBottom='1px solid transparent'; this.style.color='#2c5282'">Sparrow</a> GitHub
                    </span>
                    <span style="font-size: 13px; color: #6b7280; font-weight: 500;">Version {version}</span>
                </div>
            </div>
            """
        )

# To run this file directly for testing
if __name__ == "__main__":
    # Launch with explicitly disabled API and no documentation
    demo.launch(show_api=False, share=False)