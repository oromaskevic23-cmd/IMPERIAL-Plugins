# IMPERIAL Core — Governed Composio Adapter

**Architect / Author:** Alexander Nikolaevich Romaskevich (RomaskevicH)  
**Code:** [composio_guard.py](../src/imperial_plugins/composio_guard.py)  
**Tests:** [test_composio_guard.py](../tests/test_composio_guard.py)  
**Status:** FUNCTIONAL OFFLINE READ-ONLY TRANSPORT ADAPTER; NO REAL COMPOSIO ACCOUNT OR OWNER CRYPTO ENROLLED.

## Why we implement our own adapter

The goal is to **use** Composio's external tools, not copy its source, fork its repository, claim its brand, or create a separate unmanaged orchestration system.

Composio Connect's shared MCP endpoint is `https://connect.composio.dev/mcp`. It can discover, authenticate, and execute tools across connected applications. Connecting it directly to an unrestricted NCA would expose a broad and evolving capability surface.

The official Composio documentation says MCP-hosted tool execution **does not run local SDK `beforeExecute`/`afterExecute` hooks**. For IMPERIAL Core's application, every provider action must pass through a verified, tenant-bound gateway **before** reaching a trusted SDK/transport. Do not mistake an approval in the AI's text for cryptographic authentication.

Official documentation:
- https://docs.composio.dev/docs/composio-connect
- https://docs.composio.dev/docs/sessions-via-mcp
- https://docs.composio.dev/docs/configuring-sessions
- https://docs.composio.dev/docs/authentication

## Architecture

```text
ARCHITECT / OWNER ── signed Owner permit (from independent issuer)
    |
HANTER (Command Center; routes but is not a universal execution orchestrator)
    |
Federated Orchestrator ── Nano Core Agent ── IntentLock / Enterprise Skills
    |
Trusted server verification of AI Passport + Owner permit + kill switch
    |
GovernedComposioRead [strict toolkit/tool slug map, one-request anti-replay]
    |
Trusted, allowlisted SDK transport ── Composio session ── approved public data
    |
Bounded result ── Audit Ledger receipt ── ProofGraph ── independent QA
```

VELION is the model fabric, with MAX as a mode. ORION advises; it does not grant permissions. Maintain Zero Trust, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary.

## What code is actually implemented

1. Constructor requires a nonempty **exact tool-slug to toolkit allowlist**; no wildcard catalog, and Composio meta-execution tools cannot be used as direct delegated read actions.
2. Owner Kill Switch defaults to engaged and is rechecked before and after the transport callback.
3. AI Passport and Owner permit are **separately verified by the caller's trusted host**, not by user-submitted `approved=true` text. The adapter checks tenant, orchestrator, agent, task, action scope, request hash, nonce, tool slug, toolkit, expiry and `read:public` capability.
4. Only JSON arguments below 8 KiB and replies below 32 KiB are accepted. Sensitive argument key names are denied; secrets and unfiltered output are not recorded to the ledger.
5. Durable SQLite uniqueness enforces request-id anti-replay across adapter restarts; a failed request is not automatically repeated.
6. A genuine successful invocation of the **injected tool-specific transport callback** produces a result hash and a hash-chained audit receipt.
7. No write, send, purchase, delete, publish, permission change or arbitrary batch tool can be granted through this adapter.
8. No external credential, Composio SDK or network invocation is imported in the package itself.
9. The transport receives a JSON snapshot bound to the authorized request digest. The host's Passport and Owner verifiers are called again immediately before transport and after the read, and expiry is checked using the current clock after verification. A revoked or expired result is not returned as accepted. Unknown kill-switch state and a backward clock fail closed.

Verifier callbacks must be safe to call repeatedly for the same request: replay is reserved by the adapter's SQLite store, not consumed anew by each verification. These checks are **not** an atomic distributed revocation protocol: a state change can race the final check, a provider read already started cannot be undone, and an untrusted transport cannot be made safe by this adapter alone.

## Provider setup — NOT accomplished by this commit

- Provision a scoped Composio project key using the Owner's private secrets manager. Do not paste it in chat, logs or public source.
- Configure a **separate per-user session** with only reviewed toolkit slugs; never leave the session unrestricted. A default Composio session exposes the entire catalog unless restricted.
- Connect each app through its approved OAuth flow. Explicit consent is mandatory.
- When using session MCP, configure `no_elicitation_support_fallback="deny"` if client approval is unavailable. Prefer the SDK execution path where the IMPERIAL guard can wrap every tool call.
- Verify actual vendor tool schemas and tool classifications; do **not** map a nominally named tool to a read-only allowlist without reviewing its effect and data classification.
- Bind `verify_passport` and `verify_owner_permit` to independently audited, revocable, **real** cryptographic verifier services. The test fixtures deliberately use fake verifier callbacks and are **not owner authorizations**.
- Deploy behind an authenticated private service, enforce request timeouts and outbound egress policies, ensure process-level kill/revocation and durable centralized audit replication.
- Run an authorized real read-only Composio call, independent QA, rollback and failure tests before any service is declared production-enabled.

The adapter's `read_tool` callback is an integration point, not proof of a live Composio connection. The local SQLite audit chain is not immutable storage against an administrator. In-flight provider reads cannot be forcibly cancelled by a Python callback; process-level termination remains an unsatisfied runtime control.

**FREE_ONLY:** No payment or credits are authorized by adding code to this repository. If the provider requires billable access, obtain a separate Owner decision.

## Local verification

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_composio_guard.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Every test uses synthetic identity verifiers and an injected in-memory callback. These prove local behavior only, not service authorization, external connectivity or production NCA execution.

## Remaining release gates

- [x] Original, runnable guarded adapter committed to IMPERIAL-Plugins
- [x] Exact tool allowlist and public-read-only boundary
- [x] Replay, kill switch, expiry, tamper and secret tests
- [x] Hash-chained local audit receipt
- [ ] Real Owner-enrolled Ed25519 key and AI Passport issuer
- [ ] Restricted Composio account, SDK session, OAuth and tool review
- [ ] HANTER authenticated runtime consumer and federated worker process
- [ ] Centralized Audit Ledger and ProofGraph cross-service attestation
- [ ] Independent human security acceptance, verified emergency stop and production authorization

No Composio source, app icons or third-party repository content have been copied into IMPERIAL Core.
