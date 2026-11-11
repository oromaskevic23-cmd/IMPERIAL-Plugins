"""Read-only Render OOM event triage. No API credentials or recovery actions."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import re

ALLOWED_TYPES = {"server_failed", "server_available", "server_restarted", "deploy_ended"}
SAFE_ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{2,95}$")


def _time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("TIMESTAMP_REQUIRED")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_TIMESTAMP") from exc
    if dt.tzinfo is None:
        raise ValueError("TIMEZONE_REQUIRED")
    return dt.astimezone(timezone.utc)


def assess_render_events(service_id: str, events: list[dict], *, now: str,
                         window_hours: int = 24) -> dict:
    """Classify provider event records; no claim of current uptime.

    Event data is untrusted and may be incomplete, so a clean result is never a
    production-health certificate. No network operations occur.
    """
    if not isinstance(service_id, str) or not SAFE_ID.fullmatch(service_id):
        raise ValueError("INVALID_SERVICE_ID")
    if type(window_hours) is not int or not 1 <= window_hours <= 72:
        raise ValueError("INVALID_WINDOW")
    if not isinstance(events, list) or len(events) > 500:
        raise ValueError("INVALID_EVENT_BATCH")
    instant = _time(now)
    cutoff = instant - timedelta(hours=window_hours)
    relevant: list[tuple[datetime, str, bool]] = []
    for e in events:
        if not isinstance(e, dict) or not isinstance(e.get("type"), str):
            raise ValueError("INVALID_EVENT")
        if e["type"] not in ALLOWED_TYPES:
            continue
        ts = _time(e.get("timestamp"))
        if ts > instant + timedelta(minutes=2):
            raise ValueError("FUTURE_EVENT")
        if ts < cutoff or ts > instant:
            continue
        details = e.get("details", {})
        if not isinstance(details, dict):
            raise ValueError("INVALID_EVENT_DETAILS")
        reason = details.get("reason", {})
        if reason is None:
            reason = {}
        if not isinstance(reason, dict):
            raise ValueError("INVALID_FAILURE_REASON")
        oom = (e["type"] == "server_failed"
               and isinstance(reason.get("oomKilled"), dict)
               and bool(reason["oomKilled"].get("memoryLimit")))
        relevant.append((ts, e["type"], oom))
    relevant.sort(key=lambda x: x[0])
    oom_count = sum(1 for _, _, is_oom in relevant if is_oom)
    last_at = relevant[-1][0] if relevant else None
    if oom_count >= 2:
        status = "REPEATED_OOM"
    elif oom_count == 1:
        status = "OOM_OBSERVED"
    elif not last_at or instant - last_at > timedelta(hours=6):
        status = "INSUFFICIENT_FRESH_EVENTS"
    else:
        status = "NO_OOM_IN_PROVIDED_WINDOW"
    return {
        "schema": "imperial.render.resource.guard.v1",
        "service_id": service_id,
        "status": status,
        "oom_events": oom_count,
        "analyzed_events": len(relevant),
        "last_event_at": last_at.isoformat() if last_at else None,
        "evidence_scope": "UNTRUSTED_PROVIDER_EVENTS_ONLY",
        "production_health_verified": False,
        "recovery_authorized": False,
        "recovery_action": "REVIEW_MEMORY_AND_BUILD_FOOTPRINT_NO_AUTORESTART",
        "spend_usd": 0,
    }
