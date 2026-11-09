# IMPERIAL Core — Search Indexing MCP × Google Search Console Release Evidence

**Checkpoint:** 2026-11-04  
**Founding architect:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder • Owner • CEO.  
**Current evidence tier:** **E1 — TESTED SOURCE / CROSS-REPO CONTRACT**, not an authenticated production Google or HANTER integration.

## Completed engineering work

1. **Strict public-source MCP:** four read-only tools; two allowed GitHub Pages sites; public repository catalog only. No private project search/Google OAuth in public MCP calls.
2. **Google read bridge:** source-level verified property access, sitemap listings, Google URL Inspection response handling. Calls in tests are simulated; operator OAuth is absent.
3. **Private submission reference:** `SitemapIntent` is bound to a specific reviewed site and has an expiring owner/QA permit; Owner Kill Switch defaults to enabled and the global stop must be explicitly disabled. Independent host verifiers are injected rather than a fabricated claim of verified Owner signatures.
4. **Exact Google transport:** dedicated HTTPS `PUT` with no body, exact allowlisted endpoint, bounded response, no redirects, sanitized errors. No live provider `PUT` has been called from this repository.
5. **Persistent local state:** uniquely reserves each sitemap property; a timeout or unexpected response becomes `NEEDS_RECONCILIATION` rather than auto retry. Accepted HTTP 200/204 is labelled `GOOGLE_SITEMAP_SUBMITTED`, not `GOOGLE_INDEXED`.
6. **Audit evidence:** SQLite transactionally records `PREPARED`, `UNKNOWN_OUTCOME`, `UNCONFIRMED_HTTP` and `GOOGLE_ACCEPTED_SUBMISSION` events in a local SHA-256 hash chain. Tampering is detectable given an independent trusted anchor. This is **not** a production immutable Audit Ledger or cryptographic identity proof.
7. **Cross-repo HANTER:** an immutable plugin revision is checked out and tested through a real local MCP subprocess. A separate negative case confirms no Google writer can run while Owner Kill Switch is active.

## GitHub Actions — independently inspectable tests

### IMPERIAL-Plugins: source and simulated Google tests

**Successful workflow:** https://github.com/oromaskevic23-cmd/IMPERIAL-Plugins/actions/runs/41729959030  
**Tested source commit:** `faacf224d462cc84abac5c3f8f47d744bd71cf13`.

| Python | MCP protocol tests | Google read-adapter tests | Google submission/approval and audit tests | Result |
| --- | ---: | ---: | ---: | --- |
| 3.11 | 20 | 12 | 18 | 50/50 PASS |
| 3.12 | 20 | 12 | 18 | 50/50 PASS |

Both jobs additionally performed read-only real HTTP checks: founder sitemap **12** URLs and corporate sitemap **25** URLs, against source directories with **23** visible public technology projects.

The submission tests use a mock Google transport, mock property reader and synthetic host-verifier callbacks. **Neither Google credentials nor a real API write were used.** These results cannot be used to claim a verified Google Search Console property.

### HANTER: pinned MCP handoff and owner emergency stop

**Successful workflow:** https://github.com/oromaskevic23-cmd/HANTER-Public/actions/runs/41730375252

The HANTER workflow pins the immutable tested IMPERIAL-Plugins commit listed above, launches the stdio MCP subprocess, validates four tool names and the public project/site plan, and checks that the Google writer is denied when the Owner Kill Switch is enabled. No worker was deployed and no Google sitemap submitted.

## Release gates — precise status

| Gate | Status | Proof needed to advance |
| --- | --- | --- |
| E0 — Architecture and public/private boundary | DOCUMENTED | This specification, source and diagrams |
| E1 — Testable protocol + guarded submission source | **PASS on tested revision** | CI reports linked above |
| E2 — Owner trust/real AI Passport and independent QA | **BLOCKED** | Genuine separately provisioned cryptographic trust anchors; no test-only keys |
| E3 — Real Google OAuth + Search Console property rights | **BLOCKED** | Owner consent and verified site access returned by Google |
| E4 — Authorized sitemap PUT and reconciled provider response | **NOT EXECUTED** | Real Google API status and read-back confirmation |
| E5 — Indexed URL presence and traffic | **NOT VERIFIED** | Google URL Inspection and Search Console Performance data |
| E6 — Production HANTER 24/7 service | **NOT DEPLOYED** | Authenticated private orchestrator, persistent worker, monitoring, external audit and recovery evidence |

## Security notes and next execution

- The public MCP server remains read-only and is not an OAuth consent client; placing an access token in its public tool arguments is prohibited.
- In local source tests, a host callback can simulate approval; in production it must verify genuine short-lived Owner **Ed25519/KMS** and independent QA signatures, trusted signer identities, revocation state and scope. The actual Owner authority is not provisioned by this public repository.
- The local SQLite ledger is not distributed, cannot guarantee cross-host exactly-once effects and must not be called independently immutable. Recovery after a crashed or ambiguous provider call must use manual Google `sitemaps.list` reconciliation. Deliberate repeat submission requires separately designed and approved operation-state migration, not deleting the ledger.
- The correct Google scope for `sitemaps.submit` is `https://www.googleapis.com/auth/webmasters`. Google documents the `PUT` result as an empty response on success, not proof that search index entries exist.
- Search Console `urlInspection.index.inspect` reports **Google's indexed version**, not a live page fetch.

## Exact owner-controlled external steps remaining

1. Authenticate in https://search.google.com/search-console/ with the intended account.
2. Verify **both URL-prefix properties** exactly as defined in [the gateway specification](GOOGLE_SEARCH_CONSOLE_APPROVAL_GATEWAY.md).
3. Connect a private OAuth app that requests only the scopes needed for the approved operation. Keep access and refresh tokens in a protected private service.
4. Register verifiable and revocable Owner and independent QA signing authorities; do not reuse public test fixtures as keys.
5. After actual approval, call the separate private-host submission gate; record Google's real response and read back sitemap status. Keep the public MCP limited to read-only diagnostics.
6. Query Google URL Inspection after processing and record the actual index verdict. Do not equate successful submission with indexing.

Official reference:
- https://developers.google.com/webmaster-tools/v1/how-tos/authorizing
- https://developers.google.com/webmaster-tools/v1/sitemaps/submit
- https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect

**Architecture → Implementation → Evidence.** Do not fabricate PASS, Google indexing or commercial outcomes.
