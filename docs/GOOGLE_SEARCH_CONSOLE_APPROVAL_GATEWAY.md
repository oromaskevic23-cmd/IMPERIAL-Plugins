# IMPERIAL Search Indexing MCP — Google Search Console Approval Gateway

**Architecture authority:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder • Owner • CEO • Chief Systems Architect of IMPERIAL Core.  
**Checkpoint:** 2026-11-04.  
**Implementation classification:** Local Python reference implementation + simulated provider-response tests. **NOT CONNECTED to an authenticated Google account and NOT DEPLOYED as a public MCP service.**

## 1. Architecture before implementation

```text
Architect / final architectural decision authority
  -> HANTER AI Command Center (mission intake, evidence)
  -> Federated SEO / Publishing Orchestrator (scoped domain)
       -> AI Passport / Enterprise Skills / Guardian Core
       -> Owner Approval Gateway + independent human QA
       -> Site allowlist + public SEO checks
       -> Private Google Search Console OAuth adapter
       -> SubmissionGate and transactionally hash-linked Audit Ledger
       -> Google API sitemaps.submit (only after independent authorization)
       -> Separately verified Search Console sitemap / URL Inspection report
```

HANTER does not become a global execution orchestrator. Each domain orchestrator retains a separate tenant, runtime and authorization boundary. The MCP stdio interface remains deliberately **READ-ONLY**. The code that prepares the sitemap `PUT` is a distinct trusted-host module **not exported by public MCP tool discovery**.

## 2. Actual implemented modules

| Source | Verified behavior | Boundary |
| --- | --- | --- |
| [indexing_mcp.py](../src/imperial_plugins/indexing_mcp.py) | Four read-only MCP tools, strict public-site allowlist, XML sitemap, robots, canonical and JSON-LD checks | No Google OAuth or write tools |
| [search_console_read.py](../src/imperial_plugins/search_console_read.py) | Source-level `sites.list`, `sitemaps.list` and indexed-version URL Inspection | Needs a real private OAuth access token; none is installed here |
| [search_console_submit.py](../src/imperial_plugins/search_console_submit.py) | Separate `SitemapIntent`, external owner/QA verification hooks, short permit expiry, owner stop, actual allowlisted HTTPS PUT transport, durable SQLite local operation state and hash-linked events | Default deny; untrusted caller cannot self-authorize; no live Google submission verified |
| [test_search_console_submit.py](../tests/test_search_console_submit.py) | No real token; tests simulate successful HTTP status, timeout, permission failure, tampering and replay | A mock Google result is **not** Google evidence |

## 3. Exact Google scope

Only these two existing GitHub Pages URL-prefix sites are selectable:

| Site ID | Property URL | Sitemap URL |
| --- | --- | --- |
| `founder` | https://oromaskevic23-cmd.github.io/oromaskevic23-cmd/ | https://oromaskevic23-cmd.github.io/oromaskevic23-cmd/sitemap.xml |
| `company` | https://oromaskevic23-cmd.github.io/Capital-Core-Public/ | https://oromaskevic23-cmd.github.io/Capital-Core-Public/sitemap.xml |

No third-party property, private repository, user-entered URL, source token, payment wallet or unrelated Google account is queried by the adapter. The previously reconciled manifest documents 23 publicly disclosed technology/business projects, with seven private repositories excluded. Its inventory is a dated snapshot; no claim of automatic discovery of new repositories.

## 4. Official Google API contracts

**Read scope:** `https://www.googleapis.com/auth/webmasters.readonly` may be used for supported Search Console read methods.  
**Write scope:** `https://www.googleapis.com/auth/webmasters` is required to submit a sitemap.

To submit a sitemap, Google specifies:

```http
PUT https://www.googleapis.com/webmasters/v3/sites/{encodedSiteUrl}/sitemaps/{encodedFeedpath}
Authorization: Bearer (trusted private OAuth access token)
```

No request body is needed. Google documents an **empty response** on success. The current trusted-host submission transport accepts only HTTP 200 or 204 and records that as *submission evidence*, not evidence of crawling or indexing.

Primary references:
- https://developers.google.com/webmaster-tools/v1/how-tos/authorizing
- https://developers.google.com/webmaster-tools/v1/sitemaps/submit
- https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect

Google's restricted **Indexing API is not an appropriate substitute** for ordinary portfolio pages. Use normal sitemap discovery and independently authorized Search Console operations.

## 5. Approval Gateway invariants

The reference `SubmissionGate` defaults to **STOPPED**. For a trusted-host invocation, *all* of the following must be true:

1. The global environment stop is explicitly disabled (`IMPERIAL_OWNER_KILL_SWITCH=0`) **and** the gateway's local `kill_switch=False`. Neither setting alone grants permission.
2. The `SitemapIntent` names exactly `founder` or `company`, contains unique operation ID, owner approval evidence reference, separate independent QA reference, policy version, and bounded issue/expiry timestamps (at most 600 seconds).
3. The **private host's** `approval_verifier` authenticates the full canonical intent **AND** a distinct `qa_verifier` independently authenticates the same intent. The public repo contains **no Owner issuance key, no signed proof generator and no production trust chain**; verifier callbacks must not be replaced with unconditional acceptance in production.
4. An externally provisioned OAuth token is available **only in private host memory**. Actual Google `sites.list` reports `siteOwner` or `siteFullUser` for exactly the approved property; the Google endpoint will independently check OAuth write scope.
5. The public-site verifier returns a current, correctly scoped HTTP/sitemap/robots/canonical/catalog check.
6. A trusted Google PUT transport is **explicitly passed** by the host. There is no write-capable MCP tool or automatic private connector installation.
7. SQLite atomically reserves a single operation for the site **before** any external request. Replays or a new operation ID for an already reserved site are rejected. No ambiguous Google result triggers automatic retry.
8. Provider HTTP 200/204 yields `GOOGLE_SITEMAP_SUBMITTED`, **never** `GOOGLE_INDEXED`. Timeout, disconnection, ambiguous response or crash leave a non-retriable state requiring manual reconciliation with `sitemaps.list`.

The local `submission_events` database table is a hash-linked **tamper-evident reference**. A privileged database administrator could replace the entire database: production requires immutable external Audit Ledger anchoring, backups, forensic retention and independent QA of the provider receipt.

## 6. Trust and environment boundaries

**Public source may include:** URLs, protocol specifications, tests, synthetic approvals, exception categories, source-level evidence.

**Private, owner-controlled environment must hold:** OAuth client configuration, refresh/access tokens, Owner Ed25519/KMS signing authority, QA approver public identities, approval source of truth, encrypted durable database, cloud permissions and Google provider receipts.

Do not place OAuth secrets in ChatGPT messages, GitHub workflows/logs, public repositories, source test files or browser screenshots. Prefer an OAuth connector that keeps consent and token storage inside the provider/host and returns narrowly scoped callable access.

The current site/GSC integration tests simulate the `PUT`; they **cannot** verify current Search Console ownership, consent, actual submission or indexed URL count.

## 7. Incident response and restart

| Event | Automatic behavior | Human next action |
| --- | --- | --- |
| Owner Kill Switch active | Reject before Google request | Owner-only audited incident review |
| Permit missing/expired or QA absent | Deny | Issue genuine independently verified short permit via approved authority |
| Google property/access missing | Deny | Owner completes Google property verification / OAuth consent |
| Public sitemap inconsistent | Deny | Correct published file and repeat independent HTTP audit |
| Submission already reserved | Deny duplicate | Review journal and Google `sitemaps.list`; no blind replay |
| Provider error or timeout | Mark `NEEDS_RECONCILIATION` (or preserve `PREPARED` after process crash) | Manual provider-side reconciliation; signed override workflow is **not implemented** |
| Google 200/204 returned | Mark `GOOGLE_SITEMAP_SUBMITTED` | Read back Google sitemap status and inspect actual URL index reports; no automatic indexed claim |

## 8. Test and evidence tiers

- **E1 — SOURCE TESTED:** Real Python MCP stdio, bounded site audits, Google API read contract and guarded PUT *simulation*, negative cases, SQLite state/replay controls, local audit integrity.
- **E2 — PRIVATE AUTHORITY:** Owner Ed25519/KMS verification, independently authenticated QA, real private OAuth and verified Google property — **NOT VERIFIED**.
- **E3 — GOOGLE SUBMISSION:** Actual authorized API PUT with provider HTTP proof and Google sitemap readback — **NOT VERIFIED**.
- **E4 — INDEXING:** Google URL Inspection results for relevant canonical URLs — **NOT VERIFIED**.
- **E5 — SEARCH PERFORMANCE:** Search Console clicks/impressions/ranking evidence over time — **NOT VERIFIED**.

**Release rule:** no invented PASS; do not claim that a Google response confirms an indexed page. An approved site can still be excluded, canonicalized elsewhere or never crawled.

## 9. Reproduce locally

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_indexing_mcp.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_search_console_read.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_search_console_submit.py' -v
```

CI: [Search Indexing MCP workflow](../.github/workflows/search-indexing-mcp.yml).  
A PASS proves tested source revision only, not a deployed HANTER agent or Google account authorization.

## 9A. Post-submission reconciliation and read-only operator checks

The reference [SubmissionGate.reconcile](../src/imperial_plugins/search_console_submit.py) now performs **no second PUT**. It checks the specific authorized property through `sites.list`, queries that property's `sitemaps.list`, and compares the exact approved sitemap URL. When Google's API lists it, the local transaction receives `GOOGLE_SITEMAP_OBSERVED` with a linked audit event. That is evidence the sitemap was registered in Search Console — **never proof its constituent pages are indexed**. When Google does not list the sitemap, the outcome remains ambiguous and the operation cannot automatically retry. If the SQLite audit chain is altered, reconciliation is denied.

The [operator CLI](../tools/gsc_operator.py) provides explicit `property`, `sitemap`, `home`, `catalog` and `plan` checks for the fixed founder/company URLs. The private host must supply a **short-lived access token** through the runtime environment under `IMPERIAL_GSC_ACCESS_TOKEN`. Never pass credentials in command-line arguments, GitHub secrets/logs, user chat, or public URLs. With no token, actual checks return `GOOGLE_OAUTH_NOT_CONNECTED`. The `plan` operation is local and does not require Google access.

Example to inspect the non-mutating submission intent from a checked-out repository:

```sh
python3 tools/gsc_operator.py --site founder --check plan
python3 tools/gsc_operator.py --site company --check plan
```

These commands never submit a sitemap. For legitimate Google status checks, a **separately authorized owner-controlled runtime** must provision the access token and appropriate OAuth scope, then execute `--check property`, `--check sitemap`, `--check home` or `--check catalog` privately. No OAuth consent or token acquisition has occurred in this public repository.

## 9B. HANTER Ed25519 approval evidence

HANTER has a separate [pinned-public-key signature verifier](https://github.com/oromaskevic23-cmd/HANTER-Public/blob/main/hanter_pilot/gsc_approval_verifier.py) for two roles: **Owner** and **independent QA**. It verifies the cryptographic signatures over a domain-separated, canonical, operation-bound intent, with independent keys and issuer identities, distinct people, short validity and a fresh revocation snapshot. It supplies separate `approval_verifier` and `qa_verifier` callbacks to the existing `SubmissionGate`.

The [cross-repository CI run](https://github.com/oromaskevic23-cmd/HANTER-Public/actions/runs/41731058389) passed on Python 3.11 and 3.12 with **12 signature tests per version** and a real in-process integration using the Plugins gate. Every private key and OAuth response was synthetic; **no Owner production key is enrolled and no Google submission was performed**. Do not confuse freshly generated test signers with the verified identity of a legal owner, and do not accept a test-selected public key as a production trust root.

## 10. What unlocks the real first submission

Owner completes authorization for the precise GitHub Pages properties in Google Search Console and privately authorizes the OAuth application and its `webmasters` scope. Separately, a trusted private service must provide real verified Owner/QA signing authority, durable credentials and explicit approval. **Only then** can the `SubmissionGate` be connected to its exact allowlisted Google PUT transport. The submitted sitemap result must be retained with a Google API receipt and independently confirmed through Google Search Console.

**Architecture → Implementation → Evidence**, not permission-free automation.
