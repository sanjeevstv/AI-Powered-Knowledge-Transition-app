"""Chroma indexing and retrieval for KT RAG."""

from __future__ import annotations

import hashlib
import math
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from openai import AsyncOpenAI

from app.config import get_settings


def _pseudo_embedding(text: str, dim: int = 384) -> list[float]:
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
    x = int.from_bytes(h[:8], "big") or 1
    out: list[float] = []
    for _ in range(dim):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        out.append((x / 0x7FFFFFFF) * 2 - 1)
    norm = math.sqrt(sum(v * v for v in out)) or 1.0
    return [v / norm for v in out]


def get_collection() -> Collection:
    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return client.get_or_create_collection(
        name="kt_knowledge",
        metadata={"description": "KT transcripts, summaries, and document chunks"},
    )


def _use_openai_embeddings_api() -> bool:
    s = get_settings()
    return bool(s.openai_api_key.strip()) and not s.openai_use_pseudo_embeddings


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not _use_openai_embeddings_api():
        return [_pseudo_embedding(t) for t in texts]

    settings = get_settings()
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )
    resp = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


async def index_session_content(
    *,
    session_db_id: int,
    external_id: str,
    transcript: str,
    summary: str,
    faq_pairs: list[tuple[str, str]],
) -> None:
    """Index transcript, summary, and FAQs into Chroma with source metadata."""
    col = get_collection()
    texts: list[str] = []
    ids: list[str] = []
    metadatas: list[dict[str, Any]] = []

    def add_chunk(kind: str, idx: int, body: str) -> None:
        body = body.strip()
        if not body:
            return
        cid = f"session:{session_db_id}:{kind}:{idx}"
        ids.append(cid)
        texts.append(body)
        metadatas.append(
            {
                "source_type": "kt_session",
                "session_id": str(session_db_id),
                "external_id": external_id,
                "chunk_kind": kind,
            }
        )

    for i, ch in enumerate(chunk_text(transcript)):
        add_chunk("transcript", i, ch)
    for i, ch in enumerate(chunk_text(summary)):
        add_chunk("summary", i, ch)
    for i, (q, a) in enumerate(faq_pairs):
        add_chunk("faq", i, f"Q: {q}\nA: {a}")

    if not texts:
        return

    embeddings = await embed_texts(texts)
    col.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)


async def index_document_content(
    *,
    document_db_id: int,
    filename: str,
    body: str,
) -> None:
    col = get_collection()
    texts: list[str] = []
    ids: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for i, ch in enumerate(chunk_text(body)):
        cid = f"document:{document_db_id}:chunk:{i}"
        ids.append(cid)
        texts.append(ch)
        metadatas.append(
            {
                "source_type": "document",
                "document_id": str(document_db_id),
                "filename": filename,
                "chunk_kind": "body",
            }
        )

    if not texts:
        return

    embeddings = await embed_texts(texts)
    col.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)


async def retrieve_context(question: str, n_results: int = 5) -> tuple[list[str], list[dict[str, Any]]]:
    col = get_collection()
    settings = get_settings()
    if not _use_openai_embeddings_api():
        q_emb = _pseudo_embedding(question)
    else:
        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
        )
        resp = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=[question],
        )
        q_emb = resp.data[0].embedding

    res = col.query(query_embeddings=[q_emb], n_results=n_results)
    docs = (res.get("documents") or [[]])[0] or []
    metas = (res.get("metadatas") or [[]])[0] or []
    return list(docs), list(metas)
