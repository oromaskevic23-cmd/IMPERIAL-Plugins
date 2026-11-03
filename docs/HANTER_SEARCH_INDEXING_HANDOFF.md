# HANTER → Federated Search Orchestrator → Search Indexing MCP

**Date:** 2026-11-03  
**Founder and Chief Systems Architect:** Alexander Nikolaevich Romaskevich (RomaskevicH).  
**State:** E1 — real cross-repository MCP **source-level contract passed**; private runtime integration NOT established.

## Verified integration

The [HANTER-Public](https://github.com/oromaskevic23-cmd/HANTER-Public) repository has an actual GitHub Actions integration workflow:

- Workflow: [indexing-mcp-contract.yml](https://github.com/oromaskevic23-cmd/HANTER-Public/blob/main/.github/workflows/indexing-mcp-contract.yml)
- **Passing run:** https://github.com/oromaskevic23-cmd/HANTER-Public/actions/runs/41709759949
- Tested IMPERIAL-Plugins immutable revision: `bcfdb994652df797c8909f19d94c8e9c1d43adbe`
- Read-only execution: a local MCP stdio process is started by a HANTER-owned CI job. The job proves actual JSON-RPC `initialize`, `tools/list` and `tools/call` exchanges, parses the 23-project source registry and both sitemap plans, and verifies `UNVERIFIED` Google indexation.

This proves **real protocol interoperation between two independently versioned source repositories**, not a running HANTER NCA, Google account authorization, remote deployment, actual Google indexing or sitemap submission.

## Canonical future architecture

```text
Architect (final architectural decision authority)
  -> HANTER (AI Command Center)
     -> Regional / domain SEO Orchestrator (separate authority)
        -> AI Passport + Enterprise Skills + Guardian Core
        -> Approval Gateway for externally consequential changes
        -> Indexing MCP: bounded public-read tools
        -> Private Google Search Console adapter (source implemented, not OAuth connected)
        -> Independent QA + Audit Ledger evidence / Owner Kill Switch
```

**Federated Multi-Orchestrator Architecture** remains mandatory. HANTER is the command center, not a single global execution orchestrator. ORION is advisory intelligence. No cross-tenant or cross-runtime credentials may be inherited from an MCP test.

## Real Google API adapter (implemented and tested)

[search_console_read.py](../src/imperial_plugins/search_console_read.py) supports:
- `sites.list` for exact URL-prefix properties and verified Google-permission level;
- `sitemaps.list` for the approved property's root sitemap, returning only matching public sitemap metadata;
- `urlInspection.index.inspect` for either the official root page or catalog page, returning actual Google-reported index-status fields;
- `sitemap_submission_preflight` that produces the exact official `PUT` intent but **cannot send it**.

The bridge requires a Google OAuth access token provided only by a trusted private host; there is no OAuth consent or token in GitHub and it is **not available as a public MCP tool**. This deliberate boundary prevents an arbitrary untrusted MCP caller from reading a connected owner's private Google account.

## Gates before production

1. Owner Ed25519 enrollment and actual scoped AI Passport; the current public HMAC kernel must not be misrepresented as production identity.
2. Federated orchestrator lease and tenant-scoped Enterprise Skills, bounded to two approved public URL-prefix properties.
3. Guardian Core, Approval Gateway, Owner Kill Switch and durable Audit Ledger with independent external anchors.
4. OAuth authorization for both actual Search Console properties, with owner-controlled key storage and rotation.
5. Integrate the separately implemented, default-deny [SubmissionGate](../src/imperial_plugins/search_console_submit.py) into the trusted private runtime with real cryptographic Owner and independent-QA verifiers, a source-bound Google OAuth token, provider readback and external audit anchoring. Source-level replay protection, short expiry, Google PUT transport, local hash-linked evidence and failure reconciliation states exist and are tested with simulated provider results; they are **not yet production-authorized**.
6. URL Inspection and Page Indexing evidence from Google; audit distinguishes crawlable pages, submitted sitemap, crawled URL and indexed URL.
7. Separate functional QA, security review, release signature, rollback and publicly checkable versioned evidence.

No production deployment, automatic indexing or real NCA execution is claimed. The public site snapshot remains 23 technology/business repositories plus separate public identity and unexecuted legal planning, excluding seven private repositories. Access or even site indexing does not prove ownership of unrelated third-party software.

**Reference run:** https://github.com/oromaskevic23-cmd/IMPERIAL-Plugins/actions/runs/41709474135 — 20 MCP protocol/adversarial tests plus 12 Google read-adapter tests passed on each of Python 3.11 and 3.12, including live public HTTP checks. These Google adapter calls in tests used fabricated tokens and mocked API responses, **not a real Google authorization**.

Architecture → Implementation → Evidence.
