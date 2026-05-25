from typing import Dict, Any
from prefect import flow, task
from .sparrow_client import SparrowClient
import configparser
import logging


# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the properties file
config.read("config.properties")

# Fetch settings
query_bonds = config.get("settings-bonds", "query_bonds")


logger = logging.getLogger(__name__)


class BondsAgentError(Exception):
    """Custom exception for bonds agent processing errors"""
    pass


@task(name="extract_data")
async def extract_data(input_data: Dict[str, Any], sparrow_client: SparrowClient) -> Dict:
    """
    Extracts bonds table data from the provided document via Sparrow API.

    Args:
        input_data: Dictionary containing file content and extraction parameters
        sparrow_client: Instance of SparrowClient for API calls

    Returns:
        Dictionary containing extracted bonds data
    """
    try:
        # Inject the bonds query into extraction params
        input_data['extraction_params']['query'] = query_bonds

        result = await sparrow_client.extract_bonds_data_sparrow(input_data)

        return {
            'extracted_data': result,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error extracting bonds data: {str(e)}")
        return {
            'extracted_data': None,
            'error': str(e),
            'status': 'failed'
        }


@task(name="analyze_risk")
async def analyze_risk(extraction_result: Dict[str, Any], sparrow_client: SparrowClient) -> Dict:
    """
    Analyzes bond portfolio risk based on extracted bonds data via Sparrow Instructor pipeline.

    Args:
        extraction_result: Result dictionary from the extract_data step
        sparrow_client: Instance of SparrowClient for API calls

    Returns:
        Dictionary containing risk analysis per bond position
    """
    if extraction_result.get('status') != 'success' or not extraction_result.get('extracted_data'):
        logger.warning("Skipping risk analysis - extraction step did not produce valid data")
        return {
            'risk_analysis': None,
            'error': 'No valid extraction data available for analysis',
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
    Agent for processing bonds table documents using Sparrow API.
    """

    def __init__(self):
        self.name = "bonds"
        self.capabilities = {"document_analysis", "data_extraction"}
        self.sparrow_client = SparrowClient()

    @flow(name="bonds_flow")
    async def execute(self, input_data: Dict) -> Dict:
        """
        Main bonds document processing flow.

        Step 1 - extract_data: extracts structured bonds table data from document.
        Step 2 - analyze_risk: analyzes extracted data to identify high risk positions.

        Args:
            input_data: Dictionary containing:
                - content: raw file content (bytes)
                - filename: original filename
                - content_type: file content type
                - extraction_params: dict

        Returns:
            Dictionary containing filename, extracted bonds data, and risk analysis
        """
        extraction_result = await extract_data(input_data, self.sparrow_client)
        risk_result = await analyze_risk(extraction_result, self.sparrow_client)

        return {
            'filename': input_data['filename'],
            'extraction': extraction_result,
            'risk_analysis': risk_result
        }