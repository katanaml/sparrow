from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from prefect import flow
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Union
import base64
import json
import logging
from datetime import datetime
from celery.result import AsyncResult
from celery_config import celery_app

from base import AgentManager
from medical_prescriptions.agent import MedicalPrescriptionsAgent
from trading.agent import TradingAgent
from tasks import process_data_agent, process_file_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sparrow Agents API",
    description="Sparrow multi-agent AI system",
    openapi_url="/api/v1/sparrow-agents/openapi.json",
    docs_url="/api/v1/sparrow-agents/docs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent manager and register agents
manager = AgentManager()
manager.register_agent(MedicalPrescriptionsAgent())
manager.register_agent(TradingAgent())


class BaseRequest(BaseModel):
    """Base request model for agent execution"""
    agent_name: str = Field(..., description="Name of the agent to execute")


class FileRequest(BaseModel):
    """Request model for file-based processing"""
    agent_name: str = Field(..., description="Name of the agent to execute")
    extraction_params: Optional[Dict] = Field(
        default={"sparrow_key": "12345"},
        description="Parameters for extraction",
        json_schema_extra={
            "example": {
                "sparrow_key": "12345"
            }
        }
    )

class DataRequest(BaseModel):
    """Request model for data-based processing"""
    agent_name: str = Field(..., description="Name of the agent to execute")
    input_data: Dict = Field(
        ...,
        description="Input data for processing",
        json_schema_extra={
            "symbols": ["AAPL", "GOOGL"],
            "account_balance": 100000,
            "risk_tolerance": 0.5
        }
    )


class AgentResponse(BaseModel):
    """Standard response model"""
    flow_run_id: str = Field(..., description="Prefect flow run ID")
    status: str = Field(..., description="Execution status")
    result: Optional[Dict] = Field(None, description="Execution results")


class TaskResponse(BaseModel):
    """Response model for async task submission"""
    task_id: str = Field(..., description="Celery task ID for polling")
    status: str = Field(..., description="Initial task status")
    message: str = Field(..., description="Information message")


class TaskStatusResponse(BaseModel):
    """Response model for task status check"""
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Task status: PENDING, PROCESSING, SUCCESS, FAILURE")
    result: Optional[Dict] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress: Optional[Dict] = Field(None, description="Progress information")


@app.post("/api/v1/sparrow-agents/execute/data", response_model=AgentResponse, tags=["Execution"])
async def execute_data_agent(request: DataRequest):
    """
    Execute data-based agent processing synchronously (blocking).
    This endpoint waits for the task to complete and returns the result immediately.

    Use this endpoint when:
    - You need the result immediately
    - The task completes quickly (< 30 seconds)
    - You're willing to wait for the response

    For long-running tasks, use /execute/data/async instead.

    Example payload:
```json
    {
        "agent_name": "trading",
        "sparrow_key": "your_hex_key",
        "input_data": {
            "account_balance": 100000,
            "risk_tolerance": 0.5,
            "symbols": ["AAPL", "GOOGL"]
        }
    }
```

    Returns:
        AgentResponse with immediate results
    """
    try:
        result = await manager.execute_agent(
            request.agent_name,
            request.input_data
        )

        return AgentResponse(
            flow_run_id=str(datetime.now().timestamp()),  # Generate a unique ID
            status="success",
            result=result  # Use the result directly
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/sparrow-agents/execute/data/async", response_model=TaskResponse, tags=["Async Execution"])
async def execute_data_agent_async(request: DataRequest):
    """
    Submit data-based agent processing task asynchronously.
    Returns a task_id immediately that can be used to poll for results.

    Example payload:
```json
    {
        "agent_name": "your_agent_name",
        "input_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }
```

    After submitting, use the returned task_id with GET /api/v1/sparrow-agents/task/{task_id}
    """

    try:
        # Submit task to Celery
        task = process_data_agent.delay(
            request.agent_name,
            request.input_data
        )

        logger.info(f"Submitted async data task: {task.id} for agent: {request.agent_name}")

        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message=f"Task submitted successfully. Use GET /api/v1/sparrow-agents/task/{task.id} to check status."
        )

    except Exception as e:
        logger.error(f"Task submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@app.post("/api/v1/sparrow-agents/execute/file", response_model=AgentResponse, tags=["Execution"])
async def execute_file_agent(
        agent_name: str = Form(...),
        extraction_params: str = Form(default='{"sparrow_key": "12345"}'),
        file: UploadFile = File(...)
):
    """
    Execute file-based agent processing synchronously (blocking).
    This endpoint waits for the file processing to complete and returns the result immediately.

    Use this endpoint when:
    - You need the result immediately
    - The file is small and processes quickly
    - You're willing to wait for the response

    For large files or long processing times, use /execute/file/async instead.

    Form parameters:
    - agent_name: Name of the agent to execute (e.g., "medical_prescriptions")
    - sparrow_key: Hex string authentication key
    - extraction_params: JSON string with extraction parameters (e.g., {"extract_all": true})
    - file: PDF or image file to process

    Returns:
        AgentResponse with immediate results
    """
    try:
        file_content = await file.read()

        # Parse extraction_params from string to dict
        params = json.loads(extraction_params)

        input_data = {
            "content": file_content,
            "filename": file.filename,
            "content_type": file.content_type,
            "extraction_params": params
        }

        result = await manager.execute_agent(
            agent_name,
            input_data
        )

        return AgentResponse(
            flow_run_id=str(datetime.now().timestamp()),
            status="success",
            result=result
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/sparrow-agents/execute/file/async", response_model=TaskResponse, tags=["Async Execution"])
async def execute_file_agent_async(
        agent_name: str = Form(..., description="Name of the agent to execute"),
        extraction_params: str = Form(default='{"sparrow_key": "12345"}'),
        file: UploadFile = File(..., description="File to process")
):
    """
    Submit file-based agent processing task asynchronously.
    Returns a task_id immediately that can be used to poll for results.

    After submitting, use the returned task_id with GET /api/v1/sparrow-agents/task/{task_id}
    """
    try:
        # Read file content
        file_content = await file.read()

        # Parse extraction params
        try:
            params = json.loads(extraction_params)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid extraction_params JSON format")

        # Prepare input data
        input_data = {
            "content": file_content,
            "filename": file.filename,
            "content_type": file.content_type,
            "extraction_params": params
        }

        # Submit task to Celery
        task = process_file_agent.delay(
            agent_name,
            input_data
        )

        logger.info(f"Submitted async file task: {task.id} for agent: {agent_name}, file: {file.filename}")

        return TaskResponse(
            task_id=task.id,
            status="submitted",
            message=f"Task submitted successfully. Use GET /api/v1/sparrow-agents/task/{task.id} to check status."
        )

    except Exception as e:
        logger.error(f"Task submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@app.get("/api/v1/sparrow-agents/task/{task_id}", response_model=TaskStatusResponse, tags=["Async Execution"])
async def get_task_status(task_id: str):
    """
    Check the status of an asynchronous task.

    Status values:
    - PENDING: Task is waiting in queue
    - PROCESSING: Task is currently executing
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed with an error

    Usage:
    1. Submit a task using /execute/data/async or /execute/file/async
    2. Copy the task_id from the response
    3. Poll this endpoint with the task_id to check status
    4. When status is SUCCESS, the result field will contain the data
    """
    try:
        # Get task result from Celery
        task_result = AsyncResult(task_id, app=celery_app)

        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.state
        )

        if task_result.state == 'PENDING':
            response.progress = {'message': 'Task is waiting in queue'}

        elif task_result.state == 'PROCESSING':
            # Get progress info if available
            if task_result.info:
                response.progress = task_result.info
            else:
                response.progress = {'message': 'Task is processing'}

        elif task_result.state == 'SUCCESS':
            response.result = task_result.result

        elif task_result.state == 'FAILURE':
            # Get error information
            response.error = str(task_result.info) if task_result.info else 'Task failed with unknown error'

        else:
            # Handle other states (RETRY, REVOKED, etc.)
            response.progress = {'message': f'Task state: {task_result.state}'}

        return response

    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task status: {str(e)}")


@app.delete("/api/v1/sparrow-agents/task/{task_id}", tags=["Async Execution"])
async def cancel_task(task_id: str):
    """
    Cancel a running or pending task.

    Note: Cancellation may not be immediate for tasks that are already executing.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        task_result.revoke(terminate=True)

        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancellation requested"
        }

    except Exception as e:
        logger.error(f"Failed to cancel task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@app.get("/api/v1/sparrow-agents/agents", tags=["System"])
async def list_agents():
    """
    List all available agents and their capabilities
    """
    return {
        name: {
            "capabilities": agent.capabilities,
            "type": "file" if "document_analysis" in agent.capabilities else "data"
        }
        for name, agent in manager.agents.items()
    }


@app.get("/api/v1/sparrow-agents/health", tags=["System"])
async def health_check():
    """
    System health check
    """
    return {
        "status": "healthy",
        "agents": list(manager.agents.keys()),
        "prefect_status": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    import argparse

    # Add argument parsing for port
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8003)
    args = parser.parse_args()

    uvicorn.run("api:app", host="0.0.0.0", port=args.port, reload=True)

    # http://127.0.0.1:8003/api/v1/sparrow-agents/docs

    # Trading agent payload
    # {
    #   "agent_name": "trading",
    #   "input_data": {
    #     "account_balance": 100000,
    #     "risk_tolerance": 0.5,
    #     "symbols": [
    #       "AAPL",
    #       "GOOGL"
    #     ]
    #   }
    # }

    # Document processing agent payload
    # medical_prescriptions
    # {"extract_all": true}
