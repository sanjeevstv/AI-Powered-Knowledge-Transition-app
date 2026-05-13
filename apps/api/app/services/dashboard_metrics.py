from sqlmodel import Session, select

from app.config import Settings
from app.db.models import (
    AssessmentResult,
    ChatMessage,
    Document,
    KTSession,
    KTSessionStatus,
)
from app.schemas import DashboardSummary


def build_dashboard_summary(session: Session, settings: Settings) -> DashboardSummary:
    sessions = list(session.exec(select(KTSession)).all())
    total_sessions = len(sessions)
    completed = sum(1 for s in sessions if s.status == KTSessionStatus.completed)
    pending = total_sessions - completed
    kt_completion = (completed / total_sessions * 100) if total_sessions else 0.0

    assessments = list(session.exec(select(AssessmentResult)).all())
    assessment_count = len(assessments)
    assessment_avg = (
        sum(a.quiz_score for a in assessments) / assessment_count if assessment_count else 0.0
    )

    documents = list(session.exec(select(Document)).all())
    docs_count = len(documents)
    expected = settings.expected_documents
    doc_cov = min(100.0, (docs_count / expected * 100)) if expected else 0.0

    user_msgs = list(session.exec(select(ChatMessage).where(ChatMessage.role == "user")).all())
    asst_msgs = list(
        session.exec(select(ChatMessage).where(ChatMessage.role == "assistant")).all()
    )
    if not user_msgs:
        qa_rate = 80.0
    else:
        qa_rate = min(100.0, len(asst_msgs) / len(user_msgs) * 100.0)

    readiness = (
        0.30 * kt_completion
        + 0.30 * assessment_avg
        + 0.20 * doc_cov
        + 0.20 * qa_rate
    )

    risk_hint = (
        f"{len([s for s in sessions if s.status == KTSessionStatus.pending])} pending session(s); "
        "review SME flags on completed sessions."
    )

    return DashboardSummary(
        kt_completion_percent=round(kt_completion, 2),
        pending_sessions=pending,
        completed_sessions=completed,
        total_sessions=total_sessions,
        assessment_avg_score=round(assessment_avg, 2),
        assessment_count=assessment_count,
        document_coverage_percent=round(doc_cov, 2),
        documents_uploaded=docs_count,
        expected_documents=int(expected),
        question_resolution_rate_percent=round(qa_rate, 2),
        readiness_score=round(readiness, 2),
        open_risks_placeholder=risk_hint,
    )
