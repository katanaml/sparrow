from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from prefect import flow
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Union
import base64
import json
import logging
from datetime import datetime

from base import AgentManager
from medical_prescriptions.agent import MedicalPrescriptionsAgent
from trading.agent import TradingAgent

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


@app.post("/api/v1/sparrow-agents/execute/data", response_model=AgentResponse, tags=["Execution"])
async def execute_data_agent(request: DataRequest):
    """
    Execute data-based agent processing
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


@app.post("/api/v1/sparrow-agents/execute/file", response_model=AgentResponse, tags=["Execution"])
async def execute_file_agent(
        agent_name: str = Form(...),
        extraction_params: str = Form(default='{"sparrow_key": "12345"}'),
        file: UploadFile = File(...)
):
    """
    Execute file-based agent processing
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

    # http://127.0.0.1:8001/docs

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
