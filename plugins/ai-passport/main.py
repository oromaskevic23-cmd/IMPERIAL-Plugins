"""Minimal passport shape validation; NOT cryptographic authentication."""
def validate(passport: dict) -> bool:
    if not isinstance(passport, dict):
        return False
    return all(isinstance(passport.get(k), str) and passport[k].strip() for k in ("agent_id", "issuer", "expires_at"))
