"""
Federated AI Copilot schemas
Structured context-injection request/response models
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CopilotPageContext(BaseModel):
    page: str = Field(default="dashboard", description="Current UI page")
    prediction_id: Optional[int] = None
    round_number: Optional[int] = None
    dataset_id: Optional[int] = None
    model_id: Optional[int] = None


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    mode: str = Field(default="quick_summary", description="quick_summary|deep_analysis|governance_check|troubleshooting")
    page_context: CopilotPageContext


class CopilotReferenceLink(BaseModel):
    label: str
    url: str


class CopilotChatResponse(BaseModel):
    answer: str
    mode: str
    role: str
    context_used: Dict[str, Any]
    links: List[CopilotReferenceLink] = []
    recommendations: List[str] = []
    guardrails: List[str] = []
