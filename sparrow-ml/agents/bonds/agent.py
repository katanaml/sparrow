from typing import Dict, Any
from prefect import flow, task, get_run_logger
from .sparrow_client import SparrowClient
from tavily import TavilyClient
import logging
import json
import os
import configparser
from rich.console import Console
from rich.json import JSON

console = Console()

logger = logging.getLogger(__name__)

# Read config
config = configparser.ConfigParser()
config.read("config.properties")
tavily_api_key = config.get("settings-bonds", "tavily_api_key")


class BondsAgentError(Exception):
    """Custom exception for bonds agent processing errors"""
    pass


def _get_next_search_results_path() -> str:
    """
    Determines the next available search_results path, avoiding overwrites.
    First save is search_results.json, subsequent saves are search_results_1.json, _2.json, etc.

    Returns:
        Absolute path to use for the next search results file
    """
    base_dir = os.path.dirname(__file__)
    base_path = os.path.join(base_dir, "search_results.json")

    if not os.path.exists(base_path):
        return base_path

    suffix = 1
    while True:
        candidate_path = os.path.join(base_dir, f"search_results_{suffix}.json")
        if not os.path.exists(candidate_path):
            return candidate_path
        suffix += 1


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
async def search_positions(positions_result: Dict[str, Any], search_results_file: str = None) -> Dict:
    """
    Searches for current market information for each bond position using Tavily API.
    If search_results_file is provided, loads cached results from that file instead of calling Tavily.

    Args:
        positions_result: Result dictionary from the load_positions step
        search_results_file: Optional filename (located in the same folder as this agent) to load
            cached web search results from instead of calling Tavily

    Returns:
        Dictionary containing position data enriched with web search summaries
    """
    run_logger = get_run_logger()

    # If a cached search results file is specified, load it instead of calling Tavily
    if search_results_file:
        try:
            cached_path = os.path.join(os.path.dirname(__file__), search_results_file)
            with open(cached_path, "r") as f:
                cached_data = json.load(f)

            run_logger.info(f"Loaded cached web search results from {cached_path}")

            return {
                'enriched_positions': cached_data['enriched_positions'],
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"Error loading cached search results from {search_results_file}: {str(e)}")
            return {
                'enriched_positions': None,
                'error': str(e),
                'status': 'failed'
            }

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
                search_depth="basic",
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
                search_depth="basic",
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

        run_logger.info(f"Collected {len(enriched_positions)} enriched positions from web search")

        # Save web search results to a new file next to positions.json, never overwriting existing files
        try:
            search_results_path = _get_next_search_results_path()
            with open(search_results_path, "w") as f:
                json.dump({'enriched_positions': enriched_positions}, f, indent=2)
            run_logger.info(f"Saved web search results to {search_results_path}")
        except Exception as save_error:
            logger.error(f"Error saving web search results to file: {str(save_error)}")

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


@task(name="make_decision")
async def make_decision(positions_result: Dict[str, Any], risk_result: Dict[str, Any], search_result: Dict[str, Any], sparrow_client: SparrowClient) -> Dict:
    """
    Makes sell/hold decision for each bond position via Sparrow Instructor pipeline.
    Combines positions data, risk analysis and web search results for LLM reasoning.

    Args:
        positions_result: Result dictionary from the load_positions step
        risk_result: Result dictionary from the analyze_risk step
        search_result: Result dictionary from the search_positions step
        sparrow_client: Instance of SparrowClient for API calls

    Returns:
        Dictionary containing sell/hold decision with reasoning per position
    """
    run_logger = get_run_logger()

    if search_result.get('status') != 'success' or not search_result.get('enriched_positions'):
        run_logger.warning("Skipping decision - search positions step did not produce valid data")
        return {
            'decisions': None,
            'error': 'No valid search data available for decision making',
            'status': 'skipped'
        }

    try:
        run_logger.info("Starting sell/hold decision via Sparrow Instructor pipeline")
        result = await sparrow_client.make_decision_sparrow(
            positions_data=positions_result['extracted_data'],
            risk_data=risk_result['risk_analysis'],
            search_data=search_result['enriched_positions']
        )

        run_logger.info("Sell/hold decision completed successfully")
        return {
            'decisions': result,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error making sell/hold decision: {str(e)}")
        return {
            'decisions': None,
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
        Step 3 - search_positions: searches web for current market info per position,
            or loads cached results if search_results_file is provided in input_data.
        Step 4 - make_decision: recommends sell or hold per position based on all available data.

        Args:
            input_data: Optional dict. If it contains 'search_results_file' (e.g. "search_results_1.json"),
                step 3 loads cached web search results from that file instead of calling Tavily.

        Returns:
            Dictionary containing positions data, risk analysis, web search results and sell/hold decisions
        """
        search_results_file = (input_data or {}).get('search_results_file')

        positions_result = await load_positions()
        risk_result = await analyze_risk(positions_result, self.sparrow_client)
        search_result = await search_positions(positions_result, search_results_file)
        decision_result = await make_decision(positions_result, risk_result, search_result, self.sparrow_client)

        run_logger = get_run_logger()
        run_logger.info("Decision results:")
        console.print(JSON(json.dumps(decision_result, default=str)))

        return {
            'positions': positions_result,
            'risk_analysis': risk_result,
            'search_result': search_result,
            'decision': decision_result
        }