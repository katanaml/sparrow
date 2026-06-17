from typing import Dict, Any
from prefect import flow, task
from .sparrow_client import SparrowClient
import logging
import json
import os


logger = logging.getLogger(__name__)


class BondsAgentError(Exception):
    """Custom exception for bonds agent processing errors"""
    pass


@task(name="load_positions")
async def load_positions() -> Dict:
    """
    Loads bond positions data from positions.json file located in the same folder as this agent.

    Returns:
        Dictionary containing positions data and status
    """
    try:
        json_path = os.path.join(os.path.dirname(__file__), "positions.json")

        with open(json_path, "r") as f:
            positions = json.load(f)

        logger.info(f"Loaded {len(positions['positions'])} bond positions from {json_path}")

        return {
            'extracted_data': positions,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error loading positions data: {str(e)}")
        return {
            'extracted_data': None,
            'error': str(e),
            'status': 'failed'
        }


@task(name="analyze_risk")
async def analyze_risk(extraction_result: Dict[str, Any], sparrow_client: SparrowClient) -> Dict:
    """
    Analyzes bond portfolio risk based on positions data via Sparrow Instructor pipeline.

    Args:
        extraction_result: Result dictionary from the load_positions step
        sparrow_client: Instance of SparrowClient for API calls

    Returns:
        Dictionary containing risk analysis per bond position
    """
    if extraction_result.get('status') != 'success' or not extraction_result.get('extracted_data'):
        logger.warning("Skipping risk analysis - load positions step did not produce valid data")
        return {
            'risk_analysis': None,
            'error': 'No valid positions data available for analysis',
            'status': 'skipped'
        }

    try:
        result = await sparrow_client.analyze_bonds_risk_sparrow(
            bonds_data=extraction_result['extracted_data']
        )

        return {
            'risk_analysis': result,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error analyzing bonds risk: {str(e)}")
        return {
            'risk_analysis': None,
            'error': str(e),
            'status': 'failed'
        }


class BondsAgent:
    """
    Agent for processing bond portfolio positions using Sparrow API.
    """

    def __init__(self):
        self.name = "bonds"
        self.capabilities = {"document_analysis", "data_extraction"}
        self.sparrow_client = SparrowClient()

    @flow(name="bonds_flow")
    async def execute(self, input_data: Dict = None, **kwargs) -> Dict:
        """
        Main bonds portfolio processing flow.

        Step 1 - load_positions: loads bond positions from positions.json.
        Step 2 - analyze_risk: analyzes positions to identify high risk ones.

        Returns:
            Dictionary containing positions data and risk analysis
        """
        positions_result = await load_positions()
        risk_result = await analyze_risk(positions_result, self.sparrow_client)

        return {
            'positions': positions_result,
            'risk_analysis': risk_result
        }