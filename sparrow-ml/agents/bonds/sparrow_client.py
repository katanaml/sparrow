from typing import Dict, Any
import aiohttp
import json
from prefect import task, get_run_logger
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
options_bonds_instructor = config.get("settings-bonds", "options_bonds_instructor")


class SparrowClient:
    """
    Client for interacting with Sparrow API endpoints.
    """

    def __init__(self, base_url: str = backend_url):
        self.base_url = base_url
        self.mock_mode = False  # Set to True to return mock data

    @task(name="analyze_bonds_risk_sparrow", retries=2, timeout_seconds=3600)
    async def analyze_bonds_risk_sparrow(self, bonds_data: Dict[str, Any]) -> Dict:
        """
        Sends request to analyze bond portfolio risk using Sparrow Instructor pipeline.

        Args:
            bonds_data: Bond positions data from the load_positions step

        Returns:
            Dict containing risk analysis with fields: isin, instrument_name, loss_pct, risk_level
        """
        run_logger = get_run_logger()

        if self.mock_mode:
            run_logger.info("Running in mock mode - returning mock data")
            return {}

        # Prepare the endpoint URL
        endpoint = urljoin(self.base_url, "/api/v1/sparrow-llm/instruction-inference")

        try:
            payload_str = json.dumps(bonds_data)
            query = (
                "instruction: analyze bond portfolio and identify high risk positions based on loss percentage, "
                "return result as JSON with fields: isin, instrument_name, loss_pct, risk_level (low/medium/high), "
                f"payload: {payload_str}"
            )

            run_logger.info(f"Calling Sparrow Instructor at: {endpoint}")

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
                        result = await response.json()
                        run_logger.info("Sparrow Instructor call completed successfully")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"API call failed: {error_text}")
                        raise Exception(
                            f"Bonds risk analysis failed with status: {response.status}")
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            raise

    @task(name="make_decision_sparrow", retries=2, timeout_seconds=3600)
    async def make_decision_sparrow(self, positions_data: Dict[str, Any], risk_data: Dict[str, Any], search_data: Dict[str, Any]) -> Dict:
        """
        Sends request to make sell/hold decision for each bond position using Sparrow Instructor pipeline.

        Args:
            positions_data: Bond positions data from the load_positions step
            risk_data: Risk analysis data from the analyze_risk step
            search_data: Enriched web search data from the search_positions step

        Returns:
            Dict containing sell/hold decision with fields: isin, instrument_name, decision, reasoning
        """
        run_logger = get_run_logger()

        if self.mock_mode:
            run_logger.info("Running in mock mode - returning mock data")
            return {}

        # Prepare the endpoint URL
        endpoint = urljoin(self.base_url, "/api/v1/sparrow-llm/instruction-inference")

        try:
            payload = {
                'positions': positions_data,
                'risk_analysis': risk_data,
                'market_research': search_data
            }
            payload_str = json.dumps(payload)

            query = (
                "instruction: given bond portfolio positions with current losses, risk analysis, "
                "historical performance and market outlook, recommend sell or hold for each position. "
                "investor goal is to exit all positions to minimize capital loss before transferring funds, "
                "but is not in a hurry and can wait up to 6 months for a better exit price. "
                "hold means wait for better exit price within 6 months, sell means current loss is acceptable to exit now AND no meaningful price recovery is expected. "
                "a small current loss is not alone a reason to sell — if price recovery is likely within 6 months, hold is preferred to exit at a better price. "
                "consider: current loss percentage, recent price recovery trend, "
                "total income earned over holding period (annual_income_eur multiplied by holding_years) as offset against capital loss, "
                "and near-term price recovery potential based on market outlook, "
                "return result as JSON with fields: isin, instrument_name, decision (sell/hold), reasoning, "
                f"payload: {payload_str}"
            )

            run_logger.info(f"Calling Sparrow Instructor for sell/hold decision at: {endpoint}")

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
                        result = await response.json()
                        run_logger.info("Sell/hold decision completed successfully")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"API call failed: {error_text}")
                        raise Exception(
                            f"Sell/hold decision failed with status: {response.status}")
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            raise