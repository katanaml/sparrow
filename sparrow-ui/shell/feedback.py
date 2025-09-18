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
            <p style="text-align: center; margin-top: 8px;">
            Visit <a href="https://katanaml.io/" target="_blank">Katana ML</a> and <a href="https://github.com/katanaml/sparrow" target="_blank">Sparrow</a> GitHub for more details.
            </p>
            <p style="text-align: center; margin-top: 5px;">
            <strong>Version:</strong> {version}
            </p>
            """
        )

# To run this file directly for testing
if __name__ == "__main__":
    # Launch with explicitly disabled API and no documentation
    demo.launch(show_api=False, share=False)