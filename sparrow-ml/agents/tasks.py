"""
Celery tasks for Sparrow Agents
"""
from celery_config import celery_app
from base import AgentManager
from medical_prescriptions.agent import MedicalPrescriptionsAgent
from trading.agent import TradingAgent
import logging
import asyncio
from typing import Dict

logger = logging.getLogger(__name__)


# Initialize agent manager (this happens in the worker process)
def get_agent_manager():
    """Initialize and return configured agent manager"""
    manager = AgentManager()
    manager.register_agent(MedicalPrescriptionsAgent())
    manager.register_agent(TradingAgent())
    return manager


@celery_app.task(bind=True, name='tasks.process_data_agent')
def process_data_agent(self, agent_name: str, input_data: Dict):
    """
    Celery task for data-based agent processing

    Args:
        agent_name: Name of the agent to execute
        input_data: Input data for the agent

    Returns:
        Dict with status and result
    """
    try:
        logger.info(f"Starting data agent task: {agent_name}")
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'processing',
                'agent': agent_name,
                'progress': 0
            }
        )

        # Get agent manager
        manager = get_agent_manager()

        # Execute agent (handle async execution)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                manager.execute_agent(agent_name, input_data)
            )
        finally:
            loop.close()

        logger.info(f"Data agent task completed: {agent_name}")
        return {
            'status': 'success',
            'agent_name': agent_name,
            'result': result
        }

    except Exception as e:
        logger.error(f"Data agent task failed: {agent_name} - {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'failed',
                'agent': agent_name,
                'error': str(e)
            }
        )
        raise


@celery_app.task(bind=True, name='tasks.process_file_agent')
def process_file_agent(self, agent_name: str, input_data: Dict):
    """
    Celery task for file-based agent processing

    Args:
        agent_name: Name of the agent to execute
        input_data: Input data including file content and metadata

    Returns:
        Dict with status and result
    """
    try:
        logger.info(f"Starting file agent task: {agent_name} - {input_data.get('filename', 'unknown')}")
        self.update_state(
            state='PROCESSING',
            meta={
                'status': 'processing',
                'agent': agent_name,
                'filename': input_data.get('filename'),
                'progress': 0
            }
        )

        # Get agent manager
        manager = get_agent_manager()

        # Execute agent (handle async execution)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                manager.execute_agent(agent_name, input_data)
            )
        finally:
            loop.close()

        logger.info(f"File agent task completed: {agent_name}")
        return {
            'status': 'success',
            'agent_name': agent_name,
            'filename': input_data.get('filename'),
            'result': result
        }

    except Exception as e:
        logger.error(f"File agent task failed: {agent_name} - {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'failed',
                'agent': agent_name,
                'filename': input_data.get('filename'),
                'error': str(e)
            }
        )
        raise