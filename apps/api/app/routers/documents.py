from pathlib import Path
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlmodel import Session, select

from app.config import get_settings
from app.db.models import Document, User
from app.db.session import get_session
from app.deps import get_current_user
from app.schemas import DocumentRead
from app.services.llm import extract_text_from_pdf_bytes
from app.services.rag import index_document_content

router = APIRouter(prefix="/documents", tags=["documents"])


def _ensure_upload_dir() -> Path:
    settings = get_settings()
    p = Path(settings.data_upload_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.get("", response_model=list[DocumentRead])
def list_documents(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[Document]:
    return list(session.exec(select(Document)).all())


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
    file: UploadFile = File(...),
    tags: Annotated[
        str,
        Query(description="Comma-separated tags, e.g. runbook,sop,kt_schedule"),
    ] = "",
) -> Document:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    mime = file.content_type or "application/octet-stream"
    name = file.filename or "upload.bin"
    lower = name.lower()
    text = ""
    if lower.endswith(".txt") or mime.startswith("text/"):
        text = raw.decode("utf-8", errors="ignore")
    elif lower.endswith(".pdf") or mime == "application/pdf":
        try:
            text = extract_text_from_pdf_bytes(raw)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse PDF: {exc}") from exc

    dest_dir = _ensure_upload_dir()
    stored_name = f"{uuid.uuid4().hex}_{name}"
    dest_path = dest_dir / stored_name
    dest_path.write_bytes(raw)

    doc = Document(
        filename=name,
        mime_type=mime,
        tags=tags,
        content_extracted=text,
        storage_path=str(dest_path),
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


@router.post("/{document_id}/index", response_model=DocumentRead)
async def index_document(
    document_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Document:
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    body = doc.content_extracted or ""
    if not body.strip():
        raise HTTPException(status_code=400, detail="No extracted text to index")
    await index_document_content(document_db_id=doc.id, filename=doc.filename, body=body)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc
