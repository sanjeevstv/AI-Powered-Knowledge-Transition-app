from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db.models import ActionItem, FAQItem, KTSession, KTSessionStatus, User
from app.db.session import get_session
from app.deps import get_current_user, require_full_ui_access
from app.schemas import (
    ActionItemPatch,
    ActionItemRead,
    FAQItemRead,
    KTSessionCreate,
    KTSessionDetail,
    KTSessionRead,
    KTSessionUpdateTranscript,
    ProcessAIResponse,
)
from app.services.llm import process_kt_transcript
from app.services.rag import index_session_content

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[KTSessionRead])
def list_sessions(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[KTSession]:
    return list(session.exec(select(KTSession)).all())


@router.post("", response_model=KTSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    body: KTSessionCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_full_ui_access),
) -> KTSession:
    exists = session.exec(select(KTSession).where(KTSession.external_id == body.external_id)).first()
    if exists:
        raise HTTPException(status_code=400, detail="external_id already exists")
    sched = body.scheduled_date or datetime.utcnow()
    ks = KTSession(
        external_id=body.external_id,
        topic=body.topic,
        owner_id=body.owner_id,
        scheduled_date=sched,
        status=body.status,
    )
    session.add(ks)
    session.commit()
    session.refresh(ks)
    return ks


@router.patch("/{session_id}/action-items/{item_id}", response_model=ActionItemRead)
def patch_action_item(
    session_id: int,
    item_id: int,
    body: ActionItemPatch,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ActionItemRead:
    ai = session.get(ActionItem, item_id)
    if not ai or ai.session_id != session_id:
        raise HTTPException(status_code=404, detail="Action item not found")
    ai.is_done = body.is_done
    session.add(ai)
    session.commit()
    session.refresh(ai)
    return ActionItemRead.model_validate(ai, from_attributes=True)


@router.get("/{session_id}", response_model=KTSessionDetail)
def get_session_detail(
    session_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> KTSessionDetail:
    ks = session.get(KTSession, session_id)
    if not ks:
        raise HTTPException(status_code=404, detail="Session not found")
    actions = list(session.exec(select(ActionItem).where(ActionItem.session_id == ks.id)).all())
    faqs = list(session.exec(select(FAQItem).where(FAQItem.session_id == ks.id)).all())
    base = KTSessionRead.model_validate(ks, from_attributes=True)
    return KTSessionDetail(
        **base.model_dump(),
        action_items=[ActionItemRead.model_validate(a, from_attributes=True) for a in actions],
        faq_items=[FAQItemRead.model_validate(f, from_attributes=True) for f in faqs],
    )


@router.put("/{session_id}/transcript", response_model=KTSessionRead)
def update_transcript(
    session_id: int,
    body: KTSessionUpdateTranscript,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> KTSession:
    ks = session.get(KTSession, session_id)
    if not ks:
        raise HTTPException(status_code=404, detail="Session not found")
    ks.transcript_text = body.transcript_text
    ks.updated_at = datetime.utcnow()
    session.add(ks)
    session.commit()
    session.refresh(ks)
    return ks


@router.post("/{session_id}/process-ai", response_model=ProcessAIResponse)
async def process_ai(
    session_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> ProcessAIResponse:
    ks = session.get(KTSession, session_id)
    if not ks:
        raise HTTPException(status_code=404, detail="Session not found")
    if not ks.transcript_text.strip():
        raise HTTPException(status_code=400, detail="Transcript is empty")

    result = await process_kt_transcript(ks.transcript_text)

    for ai in session.exec(select(ActionItem).where(ActionItem.session_id == ks.id)).all():
        session.delete(ai)
    for fq in session.exec(select(FAQItem).where(FAQItem.session_id == ks.id)).all():
        session.delete(fq)
    session.commit()

    ks.summary_text = str(result.get("summary", ""))
    ks.key_decisions = str(result.get("key_decisions", ""))
    ks.risks = str(result.get("risks", ""))
    ks.missing_knowledge_notes = str(result.get("missing_knowledge", ""))
    ks.status = KTSessionStatus.completed
    ks.updated_at = datetime.utcnow()
    session.add(ks)

    for line in result.get("action_items") or []:
        if str(line).strip():
            session.add(ActionItem(session_id=ks.id, text=str(line).strip()))

    faq_count = 0
    for item in result.get("faqs") or []:
        if not isinstance(item, dict):
            continue
        q = str(item.get("question", "")).strip()
        a = str(item.get("answer", "")).strip()
        if q and a:
            session.add(FAQItem(session_id=ks.id, question=q, answer=a))
            faq_count += 1

    session.commit()
    session.refresh(ks)

    faq_pairs = [
        (f.question, f.answer)
        for f in session.exec(select(FAQItem).where(FAQItem.session_id == ks.id)).all()
    ]
    await index_session_content(
        session_db_id=ks.id,
        external_id=ks.external_id,
        transcript=ks.transcript_text,
        summary=ks.summary_text,
        faq_pairs=faq_pairs,
    )

    action_count = len(
        list(session.exec(select(ActionItem).where(ActionItem.session_id == ks.id)).all())
    )

    return ProcessAIResponse(
        session_id=ks.id,
        summary=ks.summary_text,
        key_decisions=ks.key_decisions,
        risks=ks.risks,
        action_items_created=action_count,
        faqs_created=faq_count,
        indexed_in_vector_store=True,
    )
