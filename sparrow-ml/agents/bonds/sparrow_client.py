from typing import Dict, Any
import aiohttp
import json
from prefect import task
from urllib.parse import urljoin
import logging
import configparser

logger = logging.getLogger(__name__)

# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the properties file
config.read("config.properties")

# Fetch settings
backend_url = config.get("settings-bonds", "backend_url_bonds")
options_bonds = config.get("settings-bonds", "options_bonds")
options_bonds_instructor = config.get("settings-bonds", "options_bonds_instructor")


class SparrowClient:
    """
    Client for interacting with Sparrow API endpoints.
    """

    def __init__(self, base_url: str = backend_url):
        self.base_url = base_url
        self.mock_mode = False  # Set to True to return mock data

    @task(name="extract_bonds_data_sparrow", retries=2, timeout_seconds=3600)
    async def extract_bonds_data_sparrow(self, input_data: Dict[str, Any]) -> Dict:
        """
        Sends request to extract bonds table data using Sparrow API.

        Args:
            input_data: Dictionary containing:
                - content: raw file content (bytes)
                - filename: original filename
                - content_type: file content type
                - extraction_params: dictionary of extraction parameters
                    - query: JSON schema string for bonds data extraction

        Returns:
            Dict containing the API response with extracted bonds data
        """
        if self.mock_mode:
            logger.info("Running in mock mode - returning mock data")
            return {}

        # Prepare the endpoint URL
        endpoint = urljoin(self.base_url, "/api/v1/sparrow-llm/inference")

        try:
            query = input_data['extraction_params']['query']

            # Prepare form data
            form_data = aiohttp.FormData()
            form_data.add_field('query', query)
            form_data.add_field('page_type', '')
            form_data.add_field('pipeline', 'sparrow-parse')
            form_data.add_field('options', options_bonds)
            form_data.add_field('crop_size', '')
            form_data.add_field('debug_dir', '')
            form_data.add_field('debug', 'false')
            form_data.add_field('file',
                                input_data['content'],
                                filename=input_data['filename'],
                                content_type=input_data['content_type'])

            # Make the API call
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, data=form_data, timeout=3600) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API call failed: {error_text}")
                        raise Exception(
                            f"Bonds data extraction failed with status: {response.status}")
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            raise

    @task(name="analyze_bonds_risk_sparrow", retries=2, timeout_seconds=3600)
    async def analyze_bonds_risk_sparrow(self, bonds_data: Dict[str, Any]) -> Dict:
        """
        Sends request to analyze bond portfolio risk using Sparrow Instructor pipeline.

        Args:
            bonds_data: Extracted bonds data from the previous extraction step

        Returns:
            Dict containing risk analysis with fields: instrument_short_name, loss_pct, risk_level
        """
        if self.mock_mode:
            logger.info("Running in mock mode - returning mock data")
            return {}

        # Prepare the endpoint URL
        endpoint = urljoin(self.base_url, "/api/v1/sparrow-llm/instruction-inference")

        try:
            payload_str = json.dumps(bonds_data)
            query = (
                "instruction: analyze bond portfolio and identify high risk positions based on loss percentage, "
                "return result as JSON with fields: instrument_short_name, loss_pct, risk_level (low/medium/high), "
                f"payload: {payload_str}"
            )

            # Prepare form data (instruction-inference uses form-encoded, not multipart)
            data = {
                'query': query,
                'pipeline': 'sparrow-instructor',
                'options': options_bonds_instructor,
                'debug_dir': '',
                'debug': 'false'
            }

            # Make the API call
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, data=data, timeout=3600) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API call failed: {error_text}")
                        raise Exception(
                            f"Bonds risk analysis failed with status: {response.status}")
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            raise