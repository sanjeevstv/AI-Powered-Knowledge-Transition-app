from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models import KTSessionStatus, UserRole


class HealthResponse(BaseModel):
    status: str = "ok"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    role: UserRole = UserRole.vendor_team_member


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole


class MeResponse(UserPublic):
    """Current user plus UI access derived from data/role_config.json."""

    config_role: str | None = Field(
        default=None,
        description="Role string from role_config.json for this email, if present",
    )
    ui_access: Literal["full", "limited"]


class KTSessionCreate(BaseModel):
    external_id: str = Field(examples=["KT-101"])
    topic: str
    owner_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    status: KTSessionStatus = KTSessionStatus.pending


class KTSessionUpdateTranscript(BaseModel):
    transcript_text: str


class KTSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    topic: str
    owner_id: Optional[int]
    scheduled_date: datetime
    status: KTSessionStatus
    transcript_text: str
    summary_text: str
    key_decisions: str
    risks: str
    missing_knowledge_notes: str


class ActionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    is_done: bool


class FAQItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str


class KTSessionDetail(KTSessionRead):
    action_items: list[ActionItemRead] = []
    faq_items: list[FAQItemRead] = []


class ProcessAIResponse(BaseModel):
    session_id: int
    summary: str
    key_decisions: str
    risks: str
    action_items_created: int
    faqs_created: int
    indexed_in_vector_store: bool


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    mime_type: str
    tags: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    retrieved_chunks: int
    sources: list[dict] = []


class DashboardSummary(BaseModel):
    kt_completion_percent: float
    pending_sessions: int
    completed_sessions: int
    total_sessions: int
    assessment_avg_score: float
    assessment_count: int
    document_coverage_percent: float
    documents_uploaded: int
    expected_documents: int
    question_resolution_rate_percent: float
    readiness_score: float
    open_risks_placeholder: str


class CriterionCheck(BaseModel):
    name: str
    met: bool
    detail: str


class ClosureReport(BaseModel):
    dashboard: DashboardSummary
    checklist: list[CriterionCheck]
    narrative: str
    all_criteria_met: bool


class SemanticSearchHit(BaseModel):
    snippet: str
    metadata: dict


class SemanticSearchResponse(BaseModel):
    query: str
    hits: list[SemanticSearchHit]


class ActionItemPatch(BaseModel):
    is_done: bool
