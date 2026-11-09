# IMPERIAL Core — Public Discoverability Enterprise Gate
## Verified baseline, source control, SEO-NCA preparation — 2026-11-04

**Founder, Owner, CEO / final authority:** Alexander Nikolaevich Romaskevich (RomaskevicH).  
**Release category:** E1 — public source, GitHub Actions and live public HTTP evidence. This is neither a deployed Google Search Console integration nor proof of Google's indexed URLs.

## Executive verdict

The repository-source count conflict **20/23/25** was diagnosed as a combination of a stale founder-homepage label and different object classes. An authenticated owner-scoped GitHub inventory was compared with the public API:

| Meaning | Verified count | Data boundary |
| --- | ---: | --- |
| All owner-affiliated GitHub repositories | 32 | Authenticated GitHub inventory, not public telemetry |
| Public GitHub repositories | 25 | Live public GitHub API; count and SHA-256 public-name-set fingerprint |
| Public technical/business project repositories | 23 | Curated, independently compared public inventory |
| Other public repositories (founder profile + unexecuted legal blueprint) | 2 | Excluded from the promoted project count |
| Private repositories | 7 | Authenticated owner metadata only; no names exported by public CI |
| Founder canonical sitemap URLs | 12 | Published Pages source + HTTP checks |
| IMPERIAL Core canonical sitemap URLs | 25 | Published Pages source + HTTP checks |

The **23-project count is correct** for the approved, dated technical portfolio. The former 20-project founder-page headline was stale. The published founder landing page was updated on the `gh-pages` branch at commit `e9f80ce4493bad076c4da961bfcaee5d5ae971ac` to use **23**, and three obsolete GitHub repository link aliases were replaced with currently existing first-party URLs:

- `IMPERIAL-Core-Public` → `Capital-Core-Public`
- `HANTER` → `HANTER-Public`
- `AGY---PUBLIC-` → `AGY`

These are corrections to source URLs, not claims of third-party ownership, production functionality, traffic or Google indexing.

## Live evidence

- **Founder Pages deployment:** https://github.com/oromaskevic23-cmd/oromaskevic23-cmd/actions/runs/41750660514 — SUCCESS.
- **Source, sitemap and HTTP 200 check:** https://github.com/oromaskevic23-cmd/oromaskevic23-cmd/actions/runs/41750707801 — SUCCESS; confirms both project catalogs plus 12/25 sitemap URLs.
- **Public inventory, effective root robots and simulated NCA qualification:** https://github.com/oromaskevic23-cmd/IMPERIAL-Plugins/actions/runs/41751283283 — SUCCESS.

The latter workflow passed:
- **7** adversarial offline public inventory cases;
- **6** adversarial offline root-robots cases;
- **10** offline SEO-NCA training cases, with **14** policy scenarios within the exam;
- live GitHub public API returning **25** public repositories, **23** approved projects and **2** other public repositories, with SHA-256 identifier `5d255c48d56c1002f927a329319e67d201b86bfece68538420b93fc0e4a6ed0f`;
- live `https://oromaskevic23-cmd.github.io/robots.txt` returning **HTTP 404**, treated as an absent host-root robots file for that HTTP observation.

The auditor previously looked at project files such as `/Capital-Core-Public/robots.txt`. These may exist as discoverability hints but **do not act as a host's effective robots policy**. Google defines effective robots.txt at `https://host/robots.txt`. A missing root robots file is not, by itself, an instruction forbidding crawling. It is not evidence that Google has crawled or indexed either site. Project-local sitemap declarations can still be submitted independently through Search Console after real authorization.

Google primary source: https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec

## Production gates — Source vs authority

| Level | Evidence required | Verified now? |
| --- | --- | --- |
| SOURCE_APPROVED | 23 public projects reconciled against 25 public repos | YES |
| SITE_DEPLOYED | Founder source tree, Pages deployment and public HTTP 200 | YES |
| ROOT_CRAWL_POLICY_AUDITED | Effective root-host robots URL and response checked | YES (HTTP 404 on 2026-11-04) |
| PUBLIC_SEO_MCP_TESTED | Local read-only MCP tool calls and hardened checks | YES — prior CI |
| NCA_PUBLIC_PRACTICE | Fourteen offline educational safety cases and test suite | YES |
| INDEPENDENT_NCA_EXAM | Held-out tasks and separate QA reviewer | NO |
| OWNER_SIGNED_AI_PASSPORT | Real Owner Ed25519 enrollment / signed scoped passport | NOT VERIFIED |
| GOOGLE_OWNER_VERIFIED | Both URL-prefix properties verified by Google | NOT VERIFIED |
| PRIVATE_OAUTH_CONNECTED | Secure, rotated and scoped real Search Console OAuth | NOT VERIFIED |
| SITEMAP_SUBMITTED | Provider receipt of an approved write to Google | NOT VERIFIED |
| GOOGLE_INDEXED | Actual Google URL Inspection / Pages index evidence | NOT VERIFIED |
| PRODUCTION_NCA_AUTONOMY | Durable authorized worker, incident controls and real dispatch | NOT VERIFIED |

The Search Console read adapter and the submission preflight are source-level modules. No Google Search Console token, credential or write access has been installed by this task.

## Implemented controls

### Public inventory guard

`src/imperial_plugins/public_inventory.py`

- Only fetches the GitHub public-user repository listing for the exact owner.
- Requires the approved 23 projects plus the two separately classified public repositories; new/unreviewed project visibility changes cause an explicit CI failure.
- Ignores any accidental private entry before extracting names and does not emit private names.
- Does not auto-publish any new repository, preventing accidental disclosure and mistaken association.
- Emits a SHA-256 public-name-set fingerprint, numerical counts and explicit `google_indexed=UNVERIFIED`.

`tests/test_public_inventory.py` tests a correct snapshot, new/unreviewed project, missing project, foreign owner, duplicate, private-data isolation and malformed input.

### Effective host robots guard

`src/imperial_plugins/effective_robots.py`

- Uses one immutable root-host target only; no user-provided URL reaches the network.
- Tests the host-root policy rather than a non-effective project-path `robots.txt`.
- Interprets a verified 404 as absent root robots and checks explicit 200 rules for the approved URL paths using a conservative local parser.
- Rejects ambiguous errors, redirects, unauthorized paths, oversized bodies and explicit denials.
- Does not impersonate Googlebot or claim actual indexed status.

### SEO-NCA public qualification practice

`src/imperial_plugins/seo_nca_exam.py`

- Fourteen bounded practice scenarios including: discovery-vs-indexing, root robots scope, Indexing API misuse, write approval, OAuth least privilege, private content, canonical checks, secrets handling, URL Inspection, `noindex`, unknown properties, independent QA and false Google metrics.
- Deterministic policy choices: `READ_ONLY`, `PREPARE_REVIEW`, `DENY`, `REQUIRE_APPROVAL`.
- 90% minimum and **zero critical safety failures**. Invalid/extra answers, wrong identity/version and Owner Kill Switch fail closed.
- Public practice data and reference answers are visible to code readers; passing is educational **and must never be treated as real professional certification**.
- Always returns `production_skill_granted=false`, `ai_passport_issued=false`, `independent_qa_verified=false`, and `google_api_access_granted=false`. No model inference is executed by the examiner.

## Canonical architecture and next production milestone

```text
Architect (final authority)
  -> HANTER — AI Command Center, not a global execution orchestrator
    -> Federated Search/Discoverability Orchestrator
       -> SEO NCA candidate + scoped Enterprise Skills
       -> Guardian Core + AI Passport check + Owner Kill Switch
       -> Public Search Indexing MCP (safe source checks)
       -> Independent QA + Approval Gateway (for proposed changes)
       -> Private Search Console Runtime (future authenticated work)
       -> Audit Ledger proof + rollback/incident response
```

Maintain Federated Multi-Orchestrator Architecture, Zero Trust, FREE_ONLY, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary.

**Next production steps, ordered:** real Search Console URL-prefix owner verification; independent private OAuth; actual Owner Ed25519 enrollment and replay-resistant permits; independent held-out NCA testing; first narrow approved sitemap operation with externally verifiable Google API receipt; URL Inspection state reconciliation. Do not silently bypass any gate.

## First-party sources

- [Google: robots.txt scope and HTTP semantics](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec)
- [Google: build and submit sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google: site ownership verification](https://support.google.com/webmasters/answer/9008080)
- [Google: sitemap submit API](https://developers.google.com/webmaster-tools/v1/sitemaps/submit)
- [Google: Indexing API eligibility](https://developers.google.com/search/apis/indexing-api/v3/using-api)
- [GitHub: public repository listing](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user)

Architecture → Implementation → Evidence. No false Google indexing, verified users, product adoption, real agent operations or financial returns.
