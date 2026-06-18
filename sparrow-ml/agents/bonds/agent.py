from typing import Dict, Any
from prefect import flow, task, get_run_logger
from .sparrow_client import SparrowClient
from tavily import TavilyClient
from rich.console import Console
from rich.json import JSON
import logging
import json
import os
import configparser

console = Console()


logger = logging.getLogger(__name__)

# Read config
config = configparser.ConfigParser()
config.read("config.properties")
tavily_api_key = config.get("settings-bonds", "tavily_api_key")


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
    run_logger = get_run_logger()

    try:
        json_path = os.path.join(os.path.dirname(__file__), "positions.json")

        with open(json_path, "r") as f:
            positions = json.load(f)

        run_logger.info(f"Loaded {len(positions['positions'])} bond positions from {json_path}")

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
    run_logger = get_run_logger()

    if extraction_result.get('status') != 'success' or not extraction_result.get('extracted_data'):
        run_logger.warning("Skipping risk analysis - load positions step did not produce valid data")
        return {
            'risk_analysis': None,
            'error': 'No valid positions data available for analysis',
            'status': 'skipped'
        }

    try:
        run_logger.info("Starting risk analysis via Sparrow Instructor pipeline")
        result = await sparrow_client.analyze_bonds_risk_sparrow(
            bonds_data=extraction_result['extracted_data']
        )

        run_logger.info("Risk analysis completed successfully")
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


@task(name="search_positions")
async def search_positions(positions_result: Dict[str, Any]) -> Dict:
    """
    Searches for current market information for each bond position using Tavily API.

    Args:
        positions_result: Result dictionary from the load_positions step

    Returns:
        Dictionary containing position data enriched with web search summaries
    """
    run_logger = get_run_logger()

    if positions_result.get('status') != 'success' or not positions_result.get('extracted_data'):
        run_logger.warning("Skipping web search - load positions step did not produce valid data")
        return {
            'enriched_positions': None,
            'error': 'No valid positions data available for web search',
            'status': 'skipped'
        }

    try:
        client = TavilyClient(api_key=tavily_api_key)

        enriched_positions = []
        for pos in positions_result['extracted_data']['positions']:
            instrument_name = pos['instrument_name']
            isin = pos['isin']

            # Query 1: historical performance since purchase year
            history_query = f"{isin} {instrument_name} performance history since 2018"
            run_logger.info(f"Searching history for: {history_query}")

            history_response = client.search(
                query=history_query,
                search_depth="advanced",
                max_results=3
            )
            history_summary = " ".join([
                r.get('content', '') for r in history_response.get('results', [])
            ])

            # Query 2: current outlook
            outlook_query = f"{isin} {instrument_name} outlook 2026"
            run_logger.info(f"Searching outlook for: {outlook_query}")

            outlook_response = client.search(
                query=outlook_query,
                search_depth="advanced",
                max_results=3
            )
            outlook_summary = " ".join([
                r.get('content', '') for r in outlook_response.get('results', [])
            ])

            enriched_positions.append({
                'isin': isin,
                'instrument_name': instrument_name,
                'history_summary': history_summary,
                'outlook_summary': outlook_summary
            })

        return {
            'enriched_positions': enriched_positions,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error during web search: {str(e)}")
        return {
            'enriched_positions': None,
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
        Step 3 - search_positions: searches web for current market info per position.

        Returns:
            Dictionary containing positions data, risk analysis and enriched web search results
        """
        positions_result = await load_positions()
        risk_result = await analyze_risk(positions_result, self.sparrow_client)
        search_result = await search_positions(positions_result)

        results = {
            'positions': positions_result,
            'risk_analysis': risk_result,
            'search_result': search_result
        }

        run_logger = get_run_logger()
        run_logger.info("Bonds flow results:")
        console.print(JSON(json.dumps(results, default=str)))

        return results