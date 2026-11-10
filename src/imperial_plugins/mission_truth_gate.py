"""NCA/HANTER readiness triage. Never mints approval or declares production PASS."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone


def _datetime(value):
    if not isinstance(value, str):
        raise ValueError("TIMESTAMP_REQUIRED")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_TIMESTAMP") from exc
    if result.tzinfo is None:
        raise ValueError("TIMEZONE_REQUIRED")
    return result.astimezone(timezone.utc)


def assess_nca_readiness(record: dict, *, now: str) -> dict:
    """Assess structured snapshots from a trusted read-only collector.

    All fields are still untrusted observations; the output cannot authorize
    execution, override a kill switch or independently attest signed receipts.
    """
    if not isinstance(record, dict) or set(record) != {"nca", "worker", "crm", "gate"}:
        raise ValueError("INVALID_READINESS_SCHEMA")
    for key in ("nca", "worker", "crm", "gate"):
        if not isinstance(record[key], dict):
            raise ValueError("INVALID_SECTION_" + key.upper())
    nca, worker, crm, gate = (record[k] for k in ("nca", "worker", "crm", "gate"))
    for v in ("observed_model_processes", "cron_healthy", "cron_expected"):
        if type(nca.get(v)) is not int or nca[v] < 0:
            raise ValueError("INVALID_NCA_COUNT")
    for v in ("runtime_processes",):
        if type(worker.get(v)) is not int or worker[v] < 0:
            raise ValueError("INVALID_WORKER_COUNT")
    for v in ("live_workers", "active_jobs"):
        if type(crm.get(v)) is not int or crm[v] < 0:
            raise ValueError("INVALID_CRM_COUNT")
    for source, name in ((nca, "production_authorized"),
                         (worker, "owner_kill_switch"),
                         (gate, "owner_signature_verified"),
                         (gate, "independent_qa_verified")):
        if type(source.get(name)) is not bool:
            raise ValueError("INVALID_BOOLEAN_" + name.upper())
    if not isinstance(worker.get("state"), str) or not isinstance(gate.get("gate_state"), str):
        raise ValueError("INVALID_STATE")
    instant = _datetime(now)
    checked = _datetime(nca.get("checked_at"))
    expiry = _datetime(worker.get("approval_expires_at"))
    if checked > instant + timedelta(minutes=2):
        raise ValueError("FUTURE_SNAPSHOT")
    reasons = []
    if instant - checked > timedelta(minutes=30):
        reasons.append("STALE_RUNTIME_SNAPSHOT")
    if nca["cron_expected"] == 0 or nca["cron_healthy"] != nca["cron_expected"]:
        reasons.append("SCHEDULER_NOT_FULLY_HEALTHY")
    if expiry <= instant or worker["state"] == "APPROVAL_EXPIRED":
        reasons.append("OWNER_APPROVAL_EXPIRED")
    if worker["owner_kill_switch"]:
        reasons.append("OWNER_KILL_SWITCH_ACTIVE")
    if gate["gate_state"] != "PASS":
        reasons.append("APPROVAL_GATE_NOT_PASS")
    if not gate["owner_signature_verified"]:
        reasons.append("OWNER_SIGNATURE_NOT_VERIFIED")
    if not gate["independent_qa_verified"]:
        reasons.append("INDEPENDENT_QA_NOT_VERIFIED")
    if not nca["production_authorized"]:
        reasons.append("PRODUCTION_NOT_AUTHORIZED")
    if nca["observed_model_processes"] == 0 or worker["runtime_processes"] == 0:
        reasons.append("NO_MODEL_WORKER_PROCESS")
    if crm["live_workers"] == 0:
        reasons.append("NO_LIVE_CRM_WORKER")
    if worker["runtime_processes"] > 0 and crm["live_workers"] == 0:
        reasons.append("CONFLICTING_RUNTIME_METRICS")
    stage = "BLOCKED_OR_LAB_ONLY" if reasons else "EXTERNAL_VERIFICATION_REQUIRED"
    return {"schema": "imperial.nca.truth.gate.v1", "stage": stage,
            "blockers": sorted(set(reasons)),
            "execution_authorized": False,
            "production_ready_verified": False,
            "independent_approval_proven": False,
            "evidence_scope": "SELF_REPORTED_SNAPSHOTS_NOT_ATTESTATION",
            "spend_usd": 0}
