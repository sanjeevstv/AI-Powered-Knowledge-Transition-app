from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config import get_settings
from app.db.session import get_session
from app.deps import get_current_user
from app.db.models import User
from app.schemas import ClosureReport, CriterionCheck, DashboardSummary
from app.services.dashboard_metrics import build_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> DashboardSummary:
    return build_dashboard_summary(session, get_settings())


@router.get("/closure-report", response_model=ClosureReport)
def closure_report(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ClosureReport:
    """Sample transition closure view (requirements Section 16–17)."""
    settings = get_settings()
    s = build_dashboard_summary(session, settings)

    kt_ok = s.kt_completion_percent >= 90.0
    assess_ok = s.assessment_avg_score >= 85.0
    docs_ok = s.documents_uploaded >= 1
    pending_ok = s.pending_sessions == 0
    readiness_ok = s.readiness_score >= 75.0

    checklist = [
        CriterionCheck(
            name="KT sessions completed (target ≥90%)",
            met=kt_ok,
            detail=f"{s.kt_completion_percent:.1f}% complete ({s.completed_sessions}/{s.total_sessions} sessions).",
        ),
        CriterionCheck(
            name="Assessment / knowledge absorption (target ≥85% avg)",
            met=assess_ok,
            detail=f"Average quiz score {s.assessment_avg_score:.1f}% over {s.assessment_count} record(s).",
        ),
        CriterionCheck(
            name="Critical documents in repository",
            met=docs_ok,
            detail=f"{s.documents_uploaded} document(s) uploaded (coverage vs expected {s.expected_documents}: {s.document_coverage_percent:.1f}%).",
        ),
        CriterionCheck(
            name="No pending KT sessions (proxy for open transition risk)",
            met=pending_ok,
            detail=f"{s.pending_sessions} pending session(s).",
        ),
        CriterionCheck(
            name="Composite readiness score (illustrative threshold ≥75)",
            met=readiness_ok,
            detail=f"Weighted readiness score: {s.readiness_score:.1f}.",
        ),
    ]

    met_count = sum(1 for c in checklist if c.met)
    narrative = (
        f"Transition closure snapshot: {met_count}/{len(checklist)} checklist signals are green. "
        f"Overall readiness score is {s.readiness_score:.1f}. "
        "Use KT session detail views to clear pending sessions, upload runbooks/SOPs, and drive chatbot Q&A so SME dependency drops before go-live."
    )

    return ClosureReport(
        dashboard=s,
        checklist=checklist,
        narrative=narrative,
        all_criteria_met=all(c.met for c in checklist),
    )
