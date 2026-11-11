"""IMPERIAL FUSION 500: deterministic, non-executing 500-profile plugin planner.

Founding architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
No network, imports of SDKs, token access, provider calls, worker execution or spend.
A profile is not a live worker, AI Passport, cryptographic approval or deployment.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import os
import re
from typing import Any

VERSION = "0.1.0"
PILLARS: dict[str, tuple[str, ...]] = {
    "figma": ("discovery", "design-tokens", "components", "accessibility", "design-qa"),
    "lovable": ("requirements", "frontend", "backend-contracts", "integration", "app-qa"),
    "netlify": ("build-review", "preview-plan", "security-headers", "release-qa", "rollback-plan"),
    "context7": ("library-resolution", "source-attribution", "api-contracts", "version-compatibility", "dependency-audit"),
}
ROLES = ("analyst", "architect", "builder", "verifier", "auditor")
SLOTS_PER_ROLE = 5
PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,79}$", re.ASCII)
REQUEST_FIELDS = frozenset(("task_id", "tenant_id", "orchestrator_id", "pillar", "workstream", "max_spend_usd", "requested_external_effect"))


class FusionValidationError(ValueError):
    """A request or roster fails a fail-closed contract."""


@dataclass(frozen=True, slots=True)
class AgentProfile:
    profile_id: str
    pillar: str
    squad_id: str
    workstream: str
    role: str
    slot: int
    status: str = "PROFILE_ONLY_NOT_RUNNING"


def build_roster() -> tuple[AgentProfile, ...]:
    profiles = []
    for pillar_index, (pillar, workstreams) in enumerate(PILLARS.items(), 1):
        for squad_index, workstream in enumerate(workstreams, 1):
            squad_id = f"F500-S{pillar_index:02d}{squad_index:02d}"
            for role in ROLES:
                for slot in range(1, SLOTS_PER_ROLE + 1):
                    profiles.append(AgentProfile(
                        profile_id=f"F500-{pillar.upper()}-{squad_index:02d}-{role.upper()}-{slot:02d}",
                        pillar=pillar, squad_id=squad_id, workstream=workstream,
                        role=role, slot=slot,
                    ))
    return tuple(profiles)


ROSTER = build_roster()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def roster_proof() -> dict[str, Any]:
    """Proves shape/content only; is not a signature or independent QA."""
    ids = [p.profile_id for p in ROSTER]
    squads = [p.squad_id for p in ROSTER]
    counts = dict(Counter(p.pillar for p in ROSTER))
    valid = (
        len(ROSTER) == 500 and len(set(ids)) == 500 and
        len(set(squads)) == 20 and counts == {key: 125 for key in PILLARS} and
        all(Counter(p.squad_id for p in ROSTER)[s] == 25 for s in set(squads)) and
        all(p.status == "PROFILE_ONLY_NOT_RUNNING" for p in ROSTER)
    )
    if not valid:
        raise FusionValidationError("roster invariant failed")
    return {
        "plugin": "imperial.fusion-500", "version": VERSION,
        "profile_count": len(ROSTER), "squad_count": len(set(squads)),
        "profiles_by_pillar": counts,
        "roster_sha256": hashlib.sha256(_canonical([asdict(p) for p in ROSTER])).hexdigest(),
        "verified": True, "proof_scope": "DETERMINISTIC_ROSTER_INVARIANTS_ONLY",
        "live_workers_verified": 0, "provider_connections_verified": False,
        "independent_qa_verified": False, "production_ready": False,
    }


def list_profiles(*, pillar: str, offset: int = 0, limit: int = 25) -> dict[str, Any]:
    if pillar not in PILLARS:
        raise FusionValidationError("unknown pillar")
    if type(offset) is not int or offset < 0 or offset > 125:
        raise FusionValidationError("offset out of bounds")
    if type(limit) is not int or not 1 <= limit <= 25:
        raise FusionValidationError("limit must be 1..25")
    matching = [asdict(p) for p in ROSTER if p.pillar == pillar]
    return {"pillar": pillar, "total": len(matching), "offset": offset,
            "profiles": matching[offset:offset + limit]}


def _valid_id(value: Any) -> bool:
    return type(value) is str and PATTERN.fullmatch(value) is not None


def plan_task(request: Any, *, kill_switch: bool = True) -> dict[str, Any]:
    """Create one bounded routing PROPOSAL. Never grants or performs execution.

    This module cannot authenticate the Owner, verify an AI Passport or access the
    actual Approval Gateway: those must happen separately in the private runtime.
    """
    if type(request) is not dict or set(request) != REQUEST_FIELDS:
        raise FusionValidationError("exact request fields required")
    for k in ("task_id", "tenant_id", "orchestrator_id"):
        if not _valid_id(request[k]):
            raise FusionValidationError("invalid " + k)
    pillar, workstream = request["pillar"], request["workstream"]
    if type(pillar) is not str or pillar not in PILLARS:
        raise FusionValidationError("unknown pillar")
    if type(workstream) is not str or workstream not in PILLARS[pillar]:
        raise FusionValidationError("workstream outside pillar")
    if type(request["max_spend_usd"]) is not int or request["max_spend_usd"] != 0:
        raise FusionValidationError("FREE_ONLY: max_spend_usd must be integer zero")
    if type(request["requested_external_effect"]) is not bool:
        raise FusionValidationError("requested_external_effect must be boolean")
    if type(kill_switch) is not bool:
        raise FusionValidationError("invalid kill switch state")
    # Environment kill switch overrides the caller. Only literal 0 permits
    # non-executing laboratory planning; no value ever grants real execution.
    env = os.getenv("IMPERIAL_OWNER_KILL_SWITCH")
    if kill_switch or (env is not None and env != "0"):
        return {
            "status": "BLOCKED_OWNER_KILL_SWITCH", "task_id": request["task_id"],
            "execution_authorized": False, "provider_called": False,
            "owner_signature_verified": False,
        }
    matching = [p for p in ROSTER if p.pillar == pillar and p.workstream == workstream]
    digest = hashlib.sha256(_canonical({
        "task_id": request["task_id"], "tenant_id": request["tenant_id"],
        "orchestrator_id": request["orchestrator_id"], "pillar": pillar,
        "workstream": workstream,
    })).digest()
    profile = matching[int.from_bytes(digest[:4], "big") % len(matching)]
    # A read-only documentation plan may not require release approval, but
    # provider API access is not delegated here and every external effect is gated.
    owner_approval_required = request["requested_external_effect"] or pillar == "netlify"
    return {
        "status": "PROPOSED_NOT_EXECUTED", "task_id": request["task_id"],
        "tenant_id": request["tenant_id"],
        "orchestrator_id": request["orchestrator_id"],
        "coordination_plane": "HANTER", "profile_id": profile.profile_id,
        "squad_id": profile.squad_id, "pillar": pillar,
        "workstream": workstream, "role": profile.role,
        "requires_owner_approval": bool(owner_approval_required),
        "requires_independent_qa": True,
        "requires_ai_passport": True,
        "requires_guardian_core": True,
        "requires_approval_gateway_for_effects": True,
        "requires_audit_ledger": True,
        "max_spend_usd": 0, "execution_authorized": False,
        "provider_called": False, "owner_signature_verified": False,
        "independent_qa_verified": False,
    }
