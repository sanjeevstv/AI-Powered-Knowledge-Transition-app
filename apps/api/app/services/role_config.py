"""Load email → role from data/role_config.json (UI access source of truth)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.db.models import UserRole

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _config_path() -> Path:
    return _repo_root() / "data" / "role_config.json"


def load_role_map() -> dict[str, str]:
    path = _config_path()
    if not path.exists():
        logger.warning("role_config.json missing at %s — all users get limited UI access", path)
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        out: dict[str, str] = {}
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, str):
                # Keys: lowercase email. Values: trimmed as written (Manager / SME / Vendor OK).
                out[k.strip().lower()] = v.strip()
        return out
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read role_config.json: %s", exc)
        return {}


def get_config_role_raw(email: str) -> str | None:
    """Role string from file for this email (original casing), or None if absent."""
    m = load_role_map()
    return m.get(email.strip().lower())


def canonical_role_from_config_value(value: str) -> UserRole | None:
    """
    Map human-friendly or legacy labels to UserRole.

    Full UI: Manager / Transition Manager / transition_manager (and common variants).
    Full UI: SME / sme.
    Limited: Vendor / Vendor Team Member / vendor_team_member.
    Unknown labels → None (caller treats as missing → limited UI).
    """
    v = " ".join(value.strip().split())
    if not v:
        return None
    key = v.lower()
    collapsed = "".join(ch for ch in key if ch not in " _-\t")
    spaced = " ".join(key.split())

    if key in ("manager", "transition_manager") or spaced == "transition manager":
        return UserRole.transition_manager
    if collapsed in ("manager", "transitionmanager"):
        return UserRole.transition_manager

    if key == "sme":
        return UserRole.sme

    if key in ("vendor", "vendor_team_member") or spaced == "vendor team member":
        return UserRole.vendor_team_member
    if collapsed in ("vendor", "vendorteammember"):
        return UserRole.vendor_team_member

    try:
        return UserRole(key.replace(" ", "_"))
    except ValueError:
        return None


def resolve_config_role(email: str) -> UserRole | None:
    """Role from file for this email, or None if absent or unrecognized label."""
    raw = get_config_role_raw(email)
    if not raw:
        return None
    return canonical_role_from_config_value(raw)


def ui_access_for_email(email: str) -> tuple[UserRole, str]:
    """
    Returns (effective_role_for_ui, ui_access) where ui_access is 'full' or 'limited'.
    Missing key defaults to vendor_team_member / limited.
    """
    resolved = resolve_config_role(email)
    if resolved is None:
        role = UserRole.vendor_team_member
    else:
        role = resolved
    access = (
        "full"
        if role in (UserRole.transition_manager, UserRole.sme)
        else "limited"
    )
    return role, access
