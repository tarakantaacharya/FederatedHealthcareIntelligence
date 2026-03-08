"""
Federated AI Copilot routes.
Role-aware, context-injected assistant endpoints.
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.copilot_schema import CopilotChatRequest, CopilotChatResponse
from app.services.copilot_service import CopilotService
from app.utils.auth import require_role

router = APIRouter()


@router.post("/chat", response_model=CopilotChatResponse)
def copilot_chat(
    request: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL")),
):
    """
    Context-grounded AI Copilot chat.

    Security:
    - Hospital sees only own records
    - Central (ADMIN) sees global summaries
    - No raw patient-level data returned
    """
    result = CopilotService.chat(
        db=db,
        current_user=current_user,
        message=request.message,
        mode=request.mode,
        page_context=request.page_context.dict(),
    )
    return result
