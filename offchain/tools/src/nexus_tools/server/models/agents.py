# models.py
from pydantic import BaseModel, Field
from typing import List


class ToolModel(BaseModel):
    name: str
    description: str


class AgentModel(BaseModel):
    role: str
    goal: str
    backstory: str
    tools: List[ToolModel]


class TaskModel(BaseModel):
    description: str
    expected_output: str
    agent_role: str


class CreateAgentRequest(BaseModel):
    company_description: str
    company_domain: str
    hiring_needs: str
    specific_benefits: str
    agents: List[AgentModel]
    tasks: List[TaskModel]
