"""Append-only in-memory audit event helper; production requires durable storage."""
import hashlib
import json

def chain_event(previous_hash: str, event: dict) -> dict:
    if not isinstance(previous_hash, str) or len(previous_hash) != 64:
        raise ValueError("previous_hash must be a 64-character digest")
    payload = json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256((previous_hash + payload).encode("utf-8")).hexdigest()
    return {"previous_hash": previous_hash, "event": event, "hash": digest}
