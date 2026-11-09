# IMPERIAL Core — Google Search Indexing MCP Production Checkpoint

**Checkpoint:** 2026-11-04 (Europe/Kyiv)  
**Release:** Search Indexing MCP / Search Console protected submission reference  
**Authority:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder • Owner • CEO, Final Architectural Decision Authority  
**Classification:** VERIFIED SOURCE / VERIFIED LOCAL PROTOCOL / VERIFIED SIMULATED CRYPTOGRAPHIC APPROVAL / **GOOGLE PRODUCTION NOT CONNECTED**

## Executive decision

The next engineering milestone has been completed at the **source and test-integration level**, without bypassing Owner approval, independent QA, OAuth consent or the Public/Private Boundary.

The project now has four independently inspectable components:

1. **Public read-only MCP** — a real JSON-RPC stdio process serving the 23-project public registry and two vetted GitHub Pages sites, never issuing Google writes.
2. **Google Search Console read adapter** — exact allowlisted endpoints and owner-property checks for site list, submitted sitemaps and canonical URL inspection, requiring a user-authorized private bearer token. No live token has been connected.
3. **Owner/QA-gated Google submission reference** — short-lived, exact-site sitemap intents; deny-by-default local and global kill switches; two independently verified approval callbacks; strict Google PUT transport; durable single-host SQLite operation reservation, transaction journal and replay rejection.
4. **HANTER pinned public-key proof verifier** — real Ed25519 signature verification for separate Owner and QA roles, bound to the exact operation, audience, site and policy with revocation freshness. No production Owner key, QA identity, private signer or approved credential service is installed.

Additional safeguard: after an uncertain Google network outcome, `SubmissionGate.reconcile` asks **only** `sites.list` and `sitemaps.list` on the allowed property. A listed sitemap produces a local `GOOGLE_SITEMAP_OBSERVED` record, not a claim that any URL is indexed. If the sitemap is absent, the status remains ambiguous and no PUT is retried. The local audit hash chain is verified before reconciliation.

## Reproducible tests and evidence

| Gate | Evidence | Proven scope |
| --- | --- | --- |
| Public GitHub Pages content | [Previous published-source audit](https://github.com/oromaskevic23-cmd/oromaskevic23-cmd/actions/runs/41702530969) | 12 founder sitemap URLs, 25 company sitemap URLs, core URLs HTTP 200 |
| MCP and Google adapter regression | [MCP CI SUCCESS](https://github.com/oromaskevic23-cmd/IMPERIAL-Plugins/actions/runs/41731525152) | 20 MCP + 14 Google read + 23 guarded submission tests = **57 PASS** on **each** of Python 3.11 and 3.12; two public-site HTTP audits per version |
| HANTER Ed25519 Owner/QA | [Pinned GitHub Actions CI SUCCESS](https://github.com/oromaskevic23-cmd/HANTER-Public/actions/runs/41731805301) | 12 Ed25519 security tests per Python version plus a real cross-repository integration invocation with **simulated provider** |
| General IMPERIAL plugins checks | [Repository Actions](https://github.com/oromaskevic23-cmd/IMPERIAL-Plugins/actions) | Existing plugin / security workflows; status is tied to each exact commit and should not be extrapolated |
| Real Google OAuth property access | **NOT VERIFIED** | No connected Google Search Console account |
| Google sitemap submission | **NOT EXECUTED** | No real accepted Google provider submission receipt |
| Google URL indexing | **NOT VERIFIED** | No genuine Search Console URL Inspection result |

## Immutable source map

- [MCP stdio read-only server](../src/imperial_plugins/indexing_mcp.py)
- [Dated public project site registry](../data/search-indexing-public.json)
- [Google property/status adapter](../src/imperial_plugins/search_console_read.py)
- [Guarded sitemap submission and reconciliation](../src/imperial_plugins/search_console_submit.py)
- [Private-operator read-only CLI](../tools/gsc_operator.py)
- [Google Search Console security & incident specification](GOOGLE_SEARCH_CONSOLE_APPROVAL_GATEWAY.md)
- [HANTER Ed25519 signer verification](https://github.com/oromaskevic23-cmd/HANTER-Public/blob/main/hanter_pilot/gsc_approval_verifier.py)
- [HANTER signed approval engineering specification](https://github.com/oromaskevic23-cmd/HANTER-Public/blob/main/docs/GSC_SIGNED_APPROVAL_HANDOFF.md)
- [HANTER CI pinned integration workflow](https://github.com/oromaskevic23-cmd/HANTER-Public/blob/main/.github/workflows/gsc-signed-approval-contract.yml)

## Exact authorization and production state machine

```text
PUBLIC_MCP_READ_ONLY_READY
    ↓
SITE_HTTP_AND_SITEMAP_AUDIT_VERIFIED      [Source/HTTP evidence exists]
    ↓
OWNER_ED25519_ROOT_EXTERNALLY_ENROLLED    [NOT VERIFIED]
    ↓
INDEPENDENT_QA_IDENTITY_ENROLLED          [NOT VERIFIED]
    ↓
PRIVATE_OAUTH_WEBMASTERS_CONSENT_GRANTED  [NOT VERIFIED]
    ↓
GOOGLE_EXACT_PROPERTY_ACCESS_CONFIRMED    [NOT VERIFIED]
    ↓
SHORT_LIVED_OWNER_AND_QA_APPROVAL         [NOT VERIFIED]
    ↓
PREPARED_SQLITE_OPERATION                 [REFERENCE TESTED]
    ↓
GOOGLE_SITEMAP_SUBMIT_ACCEPTED            [SIMULATED ONLY]
    ↓
GOOGLE_SITEMAP_LIST_READBACK              [SIMULATED ONLY]
    ↓
GOOGLE_URL_INSPECTION_INDEXED_STATUS      [NOT VERIFIED]
```

**Fail-closed invariant:** a self-reported PASS, fake token, local test signing key, copied proof reference or NCA prompt cannot replace real Owner identity, independent QA, Google property access or external provider evidence.

**Kill switch:** an Owner emergency stop blocks submission by default. The public MCP must never expose submit methods. No background Google monitor, paid API service or commercial financial operation has been launched.

**Reconciliation rule:** an uncertain PUT result cannot trigger automatic replay; the owner must reconcile with genuine Google Search Console metadata and independently review the local journal. An already registered sitemap does not imply a crawled URL, indexed URL or search ranking. No source-level evidence permits a claim of Google search visibility.

## Owner-controlled runbook

1. Sign in to [Google Search Console](https://search.google.com/search-console/) with the intended Google account. Verify **both** URL-prefix properties:
   - `https://oromaskevic23-cmd.github.io/oromaskevic23-cmd/`
   - `https://oromaskevic23-cmd.github.io/Capital-Core-Public/`
2. Grant the private, independently reviewed OAuth application the least privilege necessary: `webmasters.readonly` for read checks or `webmasters` only for **separately approved** sitemap submission. Keep tokens and OAuth client configuration in the trusted private host; do not paste any token into chat or commit it to GitHub.
3. Independently enrol the actual Owner public verification key and a separate QA identity through trusted private provenance and revocation controls. The public HANTER repo intentionally includes no production private keys.
4. Use the private host's Search Console read adapter to verify property permissions and current sitemap registration; first test with `python3 tools/gsc_operator.py --site founder --check plan` and `--site company --check plan` (local, no Google calls). Only an approved host should run actual token-backed property inspection.
5. When the owner explicitly approves a specific sitemap, use the private SubmissionGate and its trusted host-supplied cryptographic verifiers. Verify the external API result and reconcile via Google sitemap list. Persist signed operator evidence in a production-strength Audit Ledger.
6. Request actual Google URL Inspection and record the real index status independently. Do not fabricate `INDEXED` or claim search ranking from a successful sitemap submission.

The approved sitemap URLs are:
- `https://oromaskevic23-cmd.github.io/oromaskevic23-cmd/sitemap.xml`
- `https://oromaskevic23-cmd.github.io/Capital-Core-Public/sitemap.xml`

## Threat controls required before production

- Two separate externally attested human signer identities (different signing keys alone are insufficient), trusted public-key pinning and revocation freshness.
- Genuine AI Passport/Enterprise Skills scoped to the city/domain orchestrator and task under the **Federated Multi-Orchestrator Architecture**, not one unbounded global executor.
- Guardian Core, Approval Gateway, Owner Kill Switch, independent QA, least-privilege OAuth, network restrictions, secret rotation and protection against token exfiltration.
- Durable encrypted server-side evidence, transactionally bound operation IDs, signed release provenance, log redaction, immutable external audit anchoring, backup/restore drills, incident response and rollback.
- No user-provided arbitrary URLs or private repository exposure from this public MCP. No unrestricted Google API access, remote code execution or wallet/payment permissions.
- Separate **CRYPTO IMPERIAL Ecosystem Boundary**. IMPERIUM is a long-term architectural digital currency envisaged for AI agents worldwide, not a currently globally adopted or exchange-listed currency.

## External authority

- Google Search Console OAuth: https://developers.google.com/webmaster-tools/v1/how-tos/authorizing
- Google sitemap submission endpoint: https://developers.google.com/webmaster-tools/v1/sitemaps/submit
- Google Search Central sitemap guidance: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Google URL Inspection: https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
- Google Indexing API scope limitation: https://developers.google.com/search/apis/indexing-api/v3/using-api

**Architecture → Implementation → Evidence.** Current achievement is a tested and independently inspectable integration, not a deployed Google-indexing autopilot.
