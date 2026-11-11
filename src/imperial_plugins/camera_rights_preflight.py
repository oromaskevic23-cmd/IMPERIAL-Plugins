"""Planning-only policy preflight for permissioned video-source onboarding.

This code never opens a stream, signs a permission, or checks external rights.
A local positive result is NOT legal permission or an Approval Gateway PASS.
"""
from __future__ import annotations
from datetime import datetime, timezone
import re

ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{2,63}$")
PURPOSES = {"facility_safety", "camera_health", "environmental_monitoring"}
TYPES = {"SYNTHETIC", "AUTHORIZED_OPERATOR_CAMERA", "LICENSED_PUBLIC_METADATA"}
EVENTS = {"signal_loss", "camera_tamper", "restricted_zone_intrusion", "environmental_hazard"}
FIELDS = {"source_id", "tenant_id", "source_type", "rights_reference",
          "expires_at", "purpose", "event_types", "retention_seconds"}


def preflight_camera_source(source: dict, *, now: str) -> dict:
    """Reject unsafe intake descriptors without camera or network access."""
    denied = {"schema": "imperial.eye.rights.preflight.v1",
              "eligible_for_external_review": False,
              "stream_connection_authorized": False,
              "production_authorized": False,
              "spend_usd": 0}
    if not isinstance(source, dict) or set(source) != FIELDS:
        return {**denied, "reason": "INVALID_SOURCE_SCHEMA"}
    for key in ("source_id", "tenant_id", "rights_reference"):
        if not isinstance(source[key], str) or not ID.fullmatch(source[key]):
            return {**denied, "reason": "INVALID_SOURCE_IDENTITY"}
    if not isinstance(source["source_type"], str) or source["source_type"] not in TYPES:
        return {**denied, "reason": "UNRECOGNIZED_SOURCE_TYPE"}
    if not isinstance(source["purpose"], str) or source["purpose"] not in PURPOSES:
        return {**denied, "reason": "PROHIBITED_PURPOSE"}
    if (not isinstance(source["event_types"], list)
            or not source["event_types"]
            or any(not isinstance(x, str) or x not in EVENTS for x in source["event_types"])):
        return {**denied, "reason": "PROHIBITED_EVENT_ANALYSIS"}
    if (type(source["retention_seconds"]) is not int
            or not 0 <= source["retention_seconds"] <= 86400):
        return {**denied, "reason": "INVALID_RETENTION_LIMIT"}
    try:
        instant = datetime.fromisoformat(now.replace("Z", "+00:00"))
        expiry = datetime.fromisoformat(source["expires_at"].replace("Z", "+00:00"))
        if instant.tzinfo is None or expiry.tzinfo is None:
            raise ValueError("TIMEZONE_REQUIRED")
    except (AttributeError, TypeError, ValueError):
        return {**denied, "reason": "INVALID_PERMISSION_EXPIRY"}
    if expiry.astimezone(timezone.utc) <= instant.astimezone(timezone.utc):
        return {**denied, "reason": "RIGHTS_EXPIRED"}
    if source["source_type"] == "LICENSED_PUBLIC_METADATA" and source["retention_seconds"] != 0:
        return {**denied, "reason": "PUBLIC_METADATA_ARCHIVE_DENIED"}
    return {**denied, "eligible_for_external_review": True,
            "reason": "REQUIRES_SIGNED_OWNER_PERMIT_AND_RIGHTS_VALIDATION"}
