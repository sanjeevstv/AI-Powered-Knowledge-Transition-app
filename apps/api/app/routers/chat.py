from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db.models import ChatMessage, User
from app.db.session import get_session
from app.deps import get_current_user, get_current_user_optional
from app.schemas import ChatRequest, ChatResponse
from app.services.llm import answer_with_context
from app.services.rag import retrieve_context

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    session: Session = Depends(get_session),
    user: User | None = Depends(get_current_user_optional),
) -> ChatResponse:
    if not body.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty message")

    chunks, metas = await retrieve_context(body.message, n_results=5)
    answer = await answer_with_context(body.message, chunks)

    uid = user.id if user else None
    session.add(ChatMessage(role="user", content=body.message, user_id=uid))
    session.add(ChatMessage(role="assistant", content=answer, user_id=uid))
    session.commit()

    sources: list[dict] = []
    for m in metas:
        if isinstance(m, dict):
            sources.append(
                {
                    "source_type": m.get("source_type"),
                    "chunk_kind": m.get("chunk_kind"),
                    "external_id": m.get("external_id"),
                    "filename": m.get("filename"),
                }
            )

    return ChatResponse(answer=answer, retrieved_chunks=len(chunks), sources=sources)
