"""Load mock KT data from `data/samples` when the database is empty."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.db.models import (
    AssessmentResult,
    KTSession,
    KTSessionStatus,
    User,
    UserRole,
)
from app.deps import hash_password


def repo_root() -> Path:
    # .../apps/api/app/services/seed.py → repository root (ai_kt)
    return Path(__file__).resolve().parents[4]


def samples_dir() -> Path:
    return repo_root() / "data" / "samples"


def _read_json(name: str) -> Any:
    path = samples_dir() / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(name: str) -> str:
    path = samples_dir() / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def seed_if_empty(session: Session) -> None:
    if session.exec(select(User)).first():
        return

    demo_password = hash_password("demo123")

    users_spec = [
        ("manager@example.com", "Alice Manager", UserRole.transition_manager),
        ("sme@example.com", "John SME", UserRole.sme),
        ("vendor@example.com", "Vendor Team Member", UserRole.vendor_team_member),
        ("usera@example.com", "User A", UserRole.vendor_team_member),
        ("userb@example.com", "User B", UserRole.vendor_team_member),
    ]
    email_to_user: dict[str, User] = {}
    for email, name, role in users_spec:
        u = User(email=email, hashed_password=demo_password, full_name=name, role=role)
        session.add(u)
    session.commit()
    for email, _, _ in users_spec:
        u = session.exec(select(User).where(User.email == email)).first()
        if u:
            email_to_user[email] = u

    sessions_data = _read_json("kt_sessions.json")
    if not isinstance(sessions_data, list):
        sessions_data = []

    transcript_default = _read_text("transcript_sample.txt")

    for row in sessions_data:
        if not isinstance(row, dict):
            continue
        ext = str(row.get("external_id", "KT-UNKNOWN"))
        topic = str(row.get("topic", "General KT"))
        sme_email = str(row.get("sme_email", "sme@example.com"))
        owner = email_to_user.get(sme_email) or email_to_user["sme@example.com"]
        raw_date = row.get("scheduled_date") or "2026-05-01"
        try:
            sched = datetime.fromisoformat(str(raw_date))
        except ValueError:
            sched = datetime.utcnow()
        status_raw = str(row.get("status", "pending")).lower()
        st = KTSessionStatus.completed if status_raw == "completed" else KTSessionStatus.pending
        tr = str(row.get("transcript_text") or "")
        if not tr and ext == "KT-101":
            tr = transcript_default
        ks = KTSession(
            external_id=ext,
            topic=topic,
            owner_id=owner.id,
            scheduled_date=sched,
            status=st,
            transcript_text=tr,
        )
        session.add(ks)
    session.commit()

    assessments = _read_json("assessments.json")
    if isinstance(assessments, list):
        for row in assessments:
            if not isinstance(row, dict):
                continue
            email = str(row.get("email", ""))
            score = int(row.get("score", 0))
            u = email_to_user.get(email)
            if u:
                session.add(AssessmentResult(user_id=u.id, quiz_score=score))
        session.commit()
