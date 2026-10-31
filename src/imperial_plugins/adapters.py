"""Deterministic, non-executing Enterprise Skills plugin adapters.

These functions are offline validators and planners, not browser agents,
commercial automation or claims of independently witnessed examinations.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from .core import canonical

HASH = re.compile(r"^[a-f0-9]{64}$")


def evaluate_nca_exam(cases: list[dict], submissions: dict[str, dict],
                      *, pass_fraction: float = 1.0) -> dict:
    """Score task outputs against precommitted hashes; never call an LLM."""
    if (not isinstance(cases, list) or not cases or not isinstance(submissions, dict)
        or not isinstance(pass_fraction, (int, float))
        or isinstance(pass_fraction, bool) or not 0 < pass_fraction <= 1):
        raise ValueError("invalid exam input")
    ids = []
    results = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "case_id", "expected_sha256", "critical"}:
            raise ValueError("invalid exam case")
        case_id, digest, critical = case["case_id"], case["expected_sha256"], case["critical"]
        if (not isinstance(case_id, str) or not 3 <= len(case_id) <= 100
            or not isinstance(digest, str) or not HASH.fullmatch(digest)
            or type(critical) is not bool or case_id in ids):
            raise ValueError("invalid or duplicate case")
        ids.append(case_id)
        answer = submissions.get(case_id)
        try:
            actual = hashlib.sha256(canonical(answer)).hexdigest()
        except (ValueError, TypeError, OverflowError):
            actual = ""
        passed = hmac.compare_digest(actual, digest)
        results.append({"case_id": case_id, "passed": passed, "critical": critical})
    fraction = sum(r["passed"] for r in results) / len(results)
    certified = fraction >= pass_fraction and all(
        r["passed"] for r in results if r["critical"])
    return {"passed": certified, "fraction": fraction, "cases": results,
            "independent_qa_verified": False, "real_world_skill_proven": False}


def inspect_n8n_workflow(workflow: dict) -> dict:
    """Static risk hints only: not a substitute for reviewing executable JS."""
    if not isinstance(workflow, dict) or not isinstance(workflow.get("nodes"), list):
        raise ValueError("invalid workflow")
    reasons = []
    if workflow.get("active") is not False:
        reasons.append("workflow_not_inactive")
    if workflow.get("credentials"):
        reasons.append("embedded_credentials")
    names = []
    for node in workflow["nodes"]:
        if not isinstance(node, dict) or not isinstance(node.get("type"), str):
            raise ValueError("invalid n8n node")
        names.append(node.get("name"))
        kind = node["type"]
        if kind == "n8n-nodes-base.code":
            reasons.append("code_requires_human_review")
        elif kind == "n8n-nodes-base.httpRequest":
            reasons.append("outbound_http_requires_approval")
        elif kind not in {"n8n-nodes-base.manualTrigger", "n8n-nodes-base.noOp",
                          "n8n-nodes-base.set"}:
            reasons.append("unreviewed_node_type")
        if node.get("credentials"):
            reasons.append("node_has_credential_reference")
    if len(names) != len(set(names)):
        reasons.append("duplicate_node_name")
    return {"approved_for_unattended_execution": False,
            "static_flags": sorted(set(reasons)),
            "needs_manual_review": True}


def plan_velion_model_route(candidates: list[dict], required: list[str],
                            *, mode: str = "STANDARD") -> dict:
    """Produce a deterministic local route plan; never contact a model provider.

    MAX is a VELION mode, never a separate LLM product name.
    """
    if mode not in {"STANDARD", "MAX"}:
        raise ValueError("invalid VELION mode")
    if (not isinstance(candidates, list) or not isinstance(required, list)
        or not all(isinstance(x, str) for x in required)):
        raise ValueError("invalid route inputs")
    valid = []
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != {
            "model_id", "enabled", "capabilities", "priority"}:
            raise ValueError("invalid candidate")
        ident, enabled, caps, priority = (
            candidate["model_id"], candidate["enabled"],
            candidate["capabilities"], candidate["priority"])
        if (not isinstance(ident, str) or not ident
            or type(enabled) is not bool or not isinstance(caps, list)
            or not all(isinstance(v, str) for v in caps)
            or type(priority) is not int or priority < 0):
            raise ValueError("invalid candidate fields")
        if enabled and set(required).issubset(set(caps)):
            valid.append(candidate)
    valid.sort(key=lambda x: (x["priority"], x["model_id"]))
    return {"model_id": valid[0]["model_id"] if valid else None, "mode": mode,
            "state": "ROUTE_PLAN_ONLY", "model_invoked": False}
