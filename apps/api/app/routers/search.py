from fastapi import APIRouter, Depends, Query

from app.db.models import User
from app.deps import get_current_user
from app.schemas import SemanticSearchHit, SemanticSearchResponse
from app.services.rag import retrieve_context

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    q: str = Query(
        ...,
        min_length=1,
        description="Natural language query across indexed transcripts, summaries, FAQs, and documents",
    ),
    _: User = Depends(get_current_user),
) -> SemanticSearchResponse:
    chunks, metas = await retrieve_context(q, n_results=12)
    hits: list[SemanticSearchHit] = []
    for ch, meta in zip(chunks, metas):
        snippet = ch[:600] + ("…" if len(ch) > 600 else "")
        md = meta if isinstance(meta, dict) else {}
        hits.append(SemanticSearchHit(snippet=snippet, metadata=md))
    return SemanticSearchResponse(query=q, hits=hits)
