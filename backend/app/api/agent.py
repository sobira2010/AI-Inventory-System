"""Agent API router — provides the POST /api/agent/chat endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent_service import process_message, clear_conversation, GeminiQuotaExceeded

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Chat with the AI Inventory Agent.

    Accepts natural language commands about inventory management.
    Requires JWT authentication.
    """
    try:
        result = process_message(
            message=request.message,
            db=db,
            user_id=current_user.id,
        )

        return AgentChatResponse(
            message=result["message"],
            action=result.get("action", "unknown"),
            success=result.get("success", True),
            data=result.get("data"),
            needs_confirmation=result.get("needs_confirmation", False),
            confirmation_type=result.get("confirmation_type"),
        )

    except GeminiQuotaExceeded as e:
        detail = {
            "code": "AI_QUOTA_EXCEEDED",
            "message": e.message,
        }
        if e.retry_after_seconds is not None:
            detail["retry_after_seconds"] = e.retry_after_seconds
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent error: an unexpected error occurred.",
        )


@router.post("/clear", tags=["AI Agent"])
def clear_agent_conversation(
    current_user: User = Depends(get_current_user),
):
    """Clear the conversation history for the current user."""
    clear_conversation(current_user.id)
    return {"message": "Conversation history cleared."}
