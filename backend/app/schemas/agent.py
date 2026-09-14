"""Pydantic schemas for the AI Agent chat endpoint."""

from pydantic import BaseModel, Field
from typing import Optional, Any


class AgentChatRequest(BaseModel):
    """Request schema for the agent chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User's natural language message")


class AgentChatResponse(BaseModel):
    """Response schema for the agent chat endpoint."""
    message: str = Field(..., description="AI agent's response message")
    action: str = Field(default="unknown", description="Detected action type")
    success: bool = Field(default=True, description="Whether the operation succeeded")
    data: Optional[Any] = Field(default=None, description="Structured data from the operation")
    needs_confirmation: bool = Field(default=False, description="Whether user confirmation is needed")
    confirmation_type: Optional[str] = Field(default=None, description="Type of confirmation needed (e.g. 'delete')")
