from typing import Dict, Any
import aiohttp
from prefect import task
from urllib.parse import urljoin
import logging
import configparser
import json

logger = logging.getLogger(__name__)

# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the properties file
config.read("config.properties")

# Fetch settings
backend_url = config.get("settings-medical-prescriptions", "backend_url")
page_type = config.get("settings-medical-prescriptions", "page_type")
options_page_type = config.get("settings-medical-prescriptions", "options_page_type")


class SparrowClient:
    """
    Client for interacting with Sparrow API endpoints.
    """

    def __init__(self, base_url: str = backend_url):
        self.base_url = base_url
        self.mock_mode = False  # Set to True to return mock data

    @task(name="extract_type_per_page_sparrow", retries=2)
    async def extract_type_per_page_sparrow(self, doc: dict) -> Dict:
        """
        Sends request to extract document pages using Sparrow API

        Args:
            doc: Dictionary containing:
                - content: raw file content (bytes)
                - filename: original filename
                - content_type: file content type
                - extraction_params: dictionary of extraction parameters

        Returns:
            Dict containing the API response
        """

        if self.mock_mode:
            logger.info("Running in mock mode - returning mock data")
            return {}

        # Prepare the endpoint URL
        endpoint = urljoin(self.base_url, "/api/v1/sparrow-llm/inference")
        print(page_type)
        print(options_page_type)

        try:
            # Prepare form data
            form_data = aiohttp.FormData()
            form_data.add_field('query', "*")
            form_data.add_field('page_type', page_type)
            form_data.add_field('pipeline', 'sparrow-parse')
            form_data.add_field('options', 'mlx,mlx-community/Qwen2.5-VL-7B-Instruct-8bit')
            form_data.add_field('crop_size', '')
            form_data.add_field('debug_dir', '')
            form_data.add_field('debug', 'true')
            form_data.add_field('sparrow_key', '')
            form_data.add_field('file',
                                doc['content'],
                                filename=doc['filename'],
                                content_type=doc['content_type'])

            # Make the API call
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, data=form_data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API call failed: {error_text}")
                        raise Exception(
                            f"Document extraction failed with status: {response.status}")
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            raise