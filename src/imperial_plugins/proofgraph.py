"""ProofGraph: hash-bound LOCAL evidence only, not independent QA or PKI."""
from __future__ import annotations
import hashlib
import hmac
import re
from .core import AGENT_PATTERN, canonical

SHA = re.compile(r"^[0-9a-f]{64}$")
FIELDS = frozenset({"schema", "task_id", "agent_id", "orchestrator_id",
                    "tenant_id", "manifest_sha256", "artifact_sha256",
                    "qa_report_sha256", "previous_proof_sha256",
                    "qa_verdict_claim", "qa_provenance", "production_authorized",
                    "external_effects", "spend_usd", "proof_sha256"})

def digest_bytes(value: bytes) -> str:
    if not isinstance(value, bytes) or len(value) > 8 * 1024 * 1024:
        raise ValueError("INVALID_OR_OVERSIZE_EVIDENCE")
    return hashlib.sha256(value).hexdigest()

def create_proof_bundle(*, task_id: str, agent_id: str, orchestrator_id: str,
                        tenant_id: str, manifest_sha256: str,
                        artifact: bytes, qa_report: bytes,
                        previous_proof_sha256: str = "0" * 64) -> dict:
    for key, item in (("task", task_id), ("agent", agent_id),
                      ("orchestrator", orchestrator_id), ("tenant", tenant_id)):
        if not isinstance(item, str) or not AGENT_PATTERN.fullmatch(item):
            raise ValueError("INVALID_" + key.upper())
    if (not isinstance(manifest_sha256, str) or not SHA.fullmatch(manifest_sha256)
        or not isinstance(previous_proof_sha256, str)
        or not SHA.fullmatch(previous_proof_sha256)):
        raise ValueError("INVALID_PROOF_LINK")
    payload = {"schema": "imperial.proofgraph.local.v1", "task_id": task_id,
               "agent_id": agent_id, "orchestrator_id": orchestrator_id,
               "tenant_id": tenant_id, "manifest_sha256": manifest_sha256,
               "artifact_sha256": digest_bytes(artifact),
               "qa_report_sha256": digest_bytes(qa_report),
               "previous_proof_sha256": previous_proof_sha256,
               "qa_verdict_claim": "NOT_INDEPENDENTLY_ATTESTED",
               "qa_provenance": "UNTRUSTED_INPUT_BYTES_ONLY",
               "production_authorized": False, "external_effects": False,
               "spend_usd": 0}
    return {**payload, "proof_sha256": hashlib.sha256(canonical(payload)).hexdigest()}

def verify_proof_bundle(bundle: object, *, artifact: bytes, qa_report: bytes,
                        expected_previous: str | None = None) -> dict:
    """Verify content hashes only. Never assert QA authenticity or execution rights."""
    denied = {"integrity_verified": False, "independent_qa_verified": False,
              "production_authorized": False}
    if not isinstance(bundle, dict) or set(bundle) != FIELDS:
        return denied
    try:
        payload = {k: v for k, v in bundle.items() if k != "proof_sha256"}
        if (payload["schema"] != "imperial.proofgraph.local.v1"
            or payload["qa_verdict_claim"] != "NOT_INDEPENDENTLY_ATTESTED"
            or payload["qa_provenance"] != "UNTRUSTED_INPUT_BYTES_ONLY"
            or payload["production_authorized"] is not False
            or payload["external_effects"] is not False
            or type(payload["spend_usd"]) is not int or payload["spend_usd"] != 0):
            raise ValueError("INVALID_PROOF_SCOPE")
        for key in ("task_id", "agent_id", "orchestrator_id", "tenant_id"):
            if not isinstance(payload[key], str) or not AGENT_PATTERN.fullmatch(payload[key]):
                raise ValueError("INVALID_PROOF_IDENTITY")
        for key in ("manifest_sha256", "artifact_sha256", "qa_report_sha256",
                    "previous_proof_sha256", "proof_sha256"):
            if not isinstance(bundle[key], str) or not SHA.fullmatch(bundle[key]):
                raise ValueError("INVALID_PROOF_DIGEST")
        digest = hashlib.sha256(canonical(payload)).hexdigest()
        if (not hmac.compare_digest(digest, bundle["proof_sha256"])
            or not hmac.compare_digest(payload["artifact_sha256"], digest_bytes(artifact))
            or not hmac.compare_digest(payload["qa_report_sha256"], digest_bytes(qa_report))
            or (expected_previous is not None
                and payload["previous_proof_sha256"] != expected_previous)):
            raise ValueError("PROOF_MISMATCH")
    except (TypeError, ValueError, KeyError, OverflowError):
        return denied
    return {"integrity_verified": True, "independent_qa_verified": False,
            "production_authorized": False, "proof_sha256": bundle["proof_sha256"]}
