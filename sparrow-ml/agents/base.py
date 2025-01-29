from abc import ABC, abstractmethod
from typing import Dict, Any
from prefect import flow

class Agent(ABC):
    """
    Base agent class that defines core functionality.
    Simplified to focus on actual workflow execution.
    """
    def __init__(self, name: str):
        self.name = name
        self.capabilities = set()

    @abstractmethod
    @flow(name="agent_flow")
    def execute(self, input_data: Dict) -> Dict:
        """Main execution flow that each agent must implement"""
        pass

class AgentManager:
    """
    Manages all agents in the system. Simplified to handle basic agent
    registration and execution.
    """
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent: Agent):
        """Registers a new agent"""
        self.agents[agent.name] = agent

    async def execute_agent(self, agent_name: str, input_data: Dict) -> Dict:
        """Executes the specified agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")

        return await self.agents[agent_name].execute(input_data)