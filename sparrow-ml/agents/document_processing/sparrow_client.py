from typing import Dict, Any
import aiohttp
from prefect import task
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


class SparrowClient:
    """
    Client for interacting with Sparrow API endpoints.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.mock_mode = True  # Set to True to return mock data

    @task(name="extract_table_sparrow", retries=2)
    async def extract_table(self, page: Any) -> Dict:
        """
        Sends request to extract tabular data using Sparrow API
        """
        if self.mock_mode:
            logger.info("Running in mock mode - returning mock table data")
            return {
                "status": "mock_success",
                "table_data": {
                    "headers": ["Column1", "Column2"],
                    "rows": [
                        ["Data1", "Data2"],
                        ["Data3", "Data4"]
                    ]
                }
            }

        # Real API call (when backend is available)
        endpoint = urljoin(self.base_url, "/extract/table")
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, data={"file": page}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Table extraction failed: {response.status}")

    @task(name="extract_form_sparrow", retries=2)
    async def extract_form(self, page: Any) -> Dict:
        """
        Sends request to extract form data using Sparrow API
        """
        if self.mock_mode:
            logger.info("Running in mock mode - returning mock form data")
            return {
                "status": "mock_success",
                "form_data": {
                    "fields": {
                        "field1": "value1",
                        "field2": "value2"
                    }
                }
            }

        # Real API call (when backend is available)
        endpoint = urljoin(self.base_url, "/extract/form")
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, data={"file": page}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Form extraction failed: {response.status}")