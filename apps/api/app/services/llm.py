"""OpenAI-backed KT processing with deterministic stubs when no API key is set."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


def _parse_llm_json_object(raw: str) -> dict[str, Any] | None:
    """
    Parse JSON from model output. Some gateways/models wrap the object in ```json ... ```
    even when response_format asks for json_object, which breaks json.loads on the raw string.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _stub_process(transcript: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
    preview = " ".join(lines[:3])[:400]
    actions: list[str] = []
    lower = transcript.lower()
    if "jenkins" in lower:
        actions.append("Share Jenkins pipeline configuration with Vendor B.")
    if "rollback" in lower or "approval" in lower:
        actions.append("Document rollback approval workflow with release manager.")
    if "splunk" in lower or "log" in lower:
        actions.append("Provide Splunk dashboards and saved searches for production logs.")
    if not actions:
        actions.append("Schedule a follow-up KT session to close documentation gaps.")

    faqs = [
        {
            "question": "How is the application deployed?",
            "answer": (
                "The deployment pipeline uses Jenkins; see the KT transcript and "
                "runbooks for stage details."
                if "jenkins" in lower
                else "Refer to the deployment runbook uploaded to the knowledge repository."
            ),
        },
        {
            "question": "Where are production logs monitored?",
            "answer": (
                "Logs are monitored in Splunk as described in this KT session."
                if "splunk" in lower
                else "See the observability section of uploaded SOPs and runbooks."
            ),
        },
    ]

    missing: list[str] = []
    if "api" not in lower and "documentation" not in lower:
        missing.append("API documentation location and access controls are not explicit in this transcript.")
    if "incident" not in lower:
        missing.append("Incident management and escalation paths are not covered.")

    return {
        "summary": (
            "Automated stub summary (set OPENAI_API_KEY for live GenAI). "
            f"Captured themes from the transcript: {preview or 'No text provided.'}"
        ),
        "key_decisions": "Stub: extract decisions from transcript manually or enable OpenAI.",
        "risks": "Stub: no critical risks auto-detected without LLM; review transcript with SME.",
        "action_items": actions,
        "faqs": faqs,
        "missing_knowledge": " ".join(missing)
        if missing
        else "Stub: enable LLM for deeper gap analysis against a KT checklist.",
    }


async def process_kt_transcript(transcript: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key.strip():
        return _stub_process(transcript)

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )
    system = (
        "You are an expert knowledge-transition analyst. "
        "Return ONLY valid JSON with keys: summary (string), key_decisions (string), "
        "risks (string), action_items (array of strings), faqs (array of {question, answer}), "
        "missing_knowledge (string listing gaps or empty string)."
    )
    user = f"KT transcript:\n\n{transcript[:12000]}"
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    data = _parse_llm_json_object(raw)
    if data is None:
        logger.warning(
            "KT process-ai: model returned non-JSON or fenced JSON; using stub. Head: %s",
            raw[:200].replace("\n", " "),
        )
        return _stub_process(transcript)

    def _as_list_str(v: Any) -> list[str]:
        if isinstance(v, list):
            return [str(x) for x in v]
        return []

    faqs_out: list[dict[str, str]] = []
    for item in data.get("faqs") or []:
        if isinstance(item, dict) and "question" in item and "answer" in item:
            faqs_out.append({"question": str(item["question"]), "answer": str(item["answer"])})

    return {
        "summary": str(data.get("summary", "")).strip() or _stub_process(transcript)["summary"],
        "key_decisions": str(data.get("key_decisions", "")).strip(),
        "risks": str(data.get("risks", "")).strip(),
        "action_items": _as_list_str(data.get("action_items")) or _stub_process(transcript)["action_items"],
        "faqs": faqs_out or _stub_process(transcript)["faqs"],
        "missing_knowledge": str(data.get("missing_knowledge", "")).strip(),
    }


async def answer_with_context(question: str, context_chunks: list[str]) -> str:
    settings = get_settings()
    context = "\n\n".join(context_chunks)[:8000]
    if not settings.openai_api_key.strip():
        snippet = context_chunks[0][:500] if context_chunks else ""
        return (
            "Stub assistant (set OPENAI_API_KEY for live answers). "
            f"Top retrieved context:\n{snippet}"
        )

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer using only the provided context when possible. "
                    "If the answer is not in the context, say you do not have enough KT material."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
        temperature=0.2,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text or "No answer generated."


def extract_text_from_pdf_bytes(data: bytes) -> str:
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            parts.append(t)
    return "\n".join(parts)
