"""Enterprise Skills: isolated declarative descriptors, not executable authority."""
from __future__ import annotations
import copy
import hashlib
import re
from .core import CAPABILITIES, canonical

SKILL_ID = re.compile(r"^imperial\.skill\.[a-z][a-z0-9-]{2,63}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,100}$")
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
DOMAINS = frozenset({"CODE_ENGINEERING", "SECURITY_DEFENSIVE", "AUTOMATION_LAB",
                     "DATA_ANALYSIS", "CREATIVE_STUDIO", "OPERATIONS_LAB"})
FIELDS = frozenset({"skill_id", "version", "tenant_id", "orchestrator_id",
                   "runtime_domain", "capability", "risk_tier", "description",
                   "requires_independent_qa", "requires_owner_approval",
                   "external_effects", "spend_usd"})

def validate_enterprise_skill(value: object) -> dict:
    """Closed schema; immutable data-only skill descriptors with zero side effects."""
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError("SKILL_SCHEMA_DENIED")
    if not isinstance(value["skill_id"], str) or not SKILL_ID.fullmatch(value["skill_id"]):
        raise ValueError("SKILL_ID_DENIED")
    if not isinstance(value["version"], str) or not SEMVER.fullmatch(value["version"]):
        raise ValueError("SKILL_VERSION_DENIED")
    for label in ("tenant_id", "orchestrator_id"):
        if not isinstance(value[label], str) or not IDENT.fullmatch(value[label]):
            raise ValueError("SKILL_BOUNDARY_DENIED")
    if (not isinstance(value["runtime_domain"], str) or value["runtime_domain"] not in DOMAINS
        or not isinstance(value["capability"], str) or value["capability"] not in CAPABILITIES):
        raise ValueError("SKILL_CAPABILITY_DENIED")
    if not isinstance(value["risk_tier"], str) or value["risk_tier"] not in ("LOW", "GUARDED"):
        raise ValueError("SKILL_RISK_DENIED")
    if (type(value["requires_independent_qa"]) is not bool
        or value["requires_independent_qa"] is not True
        or type(value["requires_owner_approval"]) is not bool
        or value["requires_owner_approval"] is not True
        or value["external_effects"] is not False
        or type(value["external_effects"]) is not bool
        or type(value["spend_usd"]) is not int or value["spend_usd"] != 0):
        raise ValueError("SKILL_SAFETY_DENIED")
    description = value["description"]
    if not isinstance(description, str) or not 10 <= len(description) <= 300:
        raise ValueError("SKILL_DESCRIPTION_DENIED")
    return copy.deepcopy(value)

class EnterpriseSkillsRegistry:
    """Explicit tenant/domain-bound catalogue. Never loads or executes plugins."""
    def __init__(self):
        self._skills: dict[tuple[str, str], dict] = {}

    def register(self, descriptor: dict) -> dict:
        skill = validate_enterprise_skill(descriptor)
        key = (skill["tenant_id"], skill["skill_id"])
        if key in self._skills:
            raise ValueError("SKILL_DUPLICATE_OR_UNREVIEWED_UPDATE")
        digest = hashlib.sha256(canonical(skill)).hexdigest()
        self._skills[key] = skill
        return {"registered": True, "descriptor_sha256": digest,
                "execution_authorized": False, "independent_qa_verified": False}

    def plan(self, *, tenant_id: str, skill_id: str, orchestrator_id: str,
             runtime_domain: str, capability: str) -> dict:
        if (not isinstance(tenant_id, str) or not isinstance(skill_id, str)
            or not isinstance(orchestrator_id, str)
            or not isinstance(runtime_domain, str) or not isinstance(capability, str)):
            return {"planned": False, "reason": "SKILL_OR_BOUNDARY_DENIED",
                    "execution_authorized": False}
        skill = self._skills.get((tenant_id, skill_id))
        if (skill is None or skill["orchestrator_id"] != orchestrator_id
            or skill["runtime_domain"] != runtime_domain
            or skill["capability"] != capability):
            return {"planned": False, "reason": "SKILL_OR_BOUNDARY_DENIED",
                    "execution_authorized": False}
        return {"planned": True, "reason": "SKILL_DESCRIPTOR_MATCH_ONLY",
                "skill_id": skill_id,
                "descriptor_sha256": hashlib.sha256(canonical(skill)).hexdigest(),
                "requires_independent_qa": True, "requires_owner_approval": True,
                "execution_authorized": False, "independent_qa_verified": False}

    def snapshot(self) -> list[dict]:
        return [copy.deepcopy(self._skills[k]) for k in sorted(self._skills)]
