"""IMPERIAL Core Guardian policy plugin. No external side effects."""
from typing import Mapping

ALLOWED_ACTIONS = frozenset({"read:public", "simulate:task"})

def evaluate(request: Mapping) -> dict:
    action = request.get("action")
    passport = request.get("ai_passport")
    approved = request.get("approval") is True
    if not isinstance(passport, str) or not passport.strip():
        return {"allowed": False, "reason": "missing_ai_passport"}
    if action not in ALLOWED_ACTIONS:
        return {"allowed": False, "reason": "action_not_allowlisted"}
    if action != "read:public" and not approved:
        return {"allowed": False, "reason": "approval_required"}
    return {"allowed": True, "reason": "policy_passed"}
