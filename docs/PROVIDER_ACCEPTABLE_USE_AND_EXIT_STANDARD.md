# IMPERIAL Core — Provider Acceptable Use, Quota and Exit Standard

**Owner / Final Architectural Authority:** Alexander Nikolaevich Romaskevich (RomaskevicH)  
**Scope:** HANTER, federated Orchestrators, Nano Core Agents, Enterprise Skills, Plugins, MCP, CONSTRUCTOR AI, CRM-SOFFT, and provider adapters.  
**Principle:** Architecture Before Implementation; FREE_ONLY until separate Owner approval.

## 1. Non-negotiable controls

1. **Provider-native quotas remain provider-native.** Do not relay, resell, expose as a standalone API, or pool a hosting provider's bundled AI allowance through third-party-compatible `/v1/models`, `/v1/chat/completions`, or equivalent endpoints without explicit provider authorization.
2. **Explicit provider rights.** Every outbound LLM/MCP integration needs an approved provider/API use case, current terms review, credentials issued for that use case, rate/budget controls, and a recorded owner. Ordinary use of an API endpoint does not grant a right to redistribute the upstream allowance.
3. **Pre-deployment gate.** Before enabling public endpoints or an NCA fleet, review authentication, tenant isolation, egress, rate limits, secrets, resale/relay risk, third-party licensing, acceptable-use terms, payment authority, privacy, and abuse handling.
4. **Zero Trust.** Enforce AI Passport, Enterprise Skills, Guardian Core, Approval Gateway, Audit Ledger, Public/Private Boundary, CRYPTO IMPERIAL Ecosystem Boundary and Owner Kill Switch. The Owner cannot override third-party acceptable-use terms.
5. **No stealth failover.** Do not bypass bans or quotas with rotated accounts, proxy relays, or unapproved identity changes. A provider suspension triggers fail-closed behavior and authorized appeal/export.
6. **No unauthorized finance.** No credit card, paid tier, payment transaction, fund conversion, or commercial contact without independently established authority and the appropriate approval.

## 2. Provider quotas and guard states

Track per-provider quotas, billing period, daily/rolling usage, restrictions, rate limits, account notices, and authorized data-export paths. Never infer that a healthy API means compliance.

For the **Supabase Free database quota**, use internal operational bands (not provider requirements):
- Below 70%: normal nonessential telemetry.
- 70–79%: early warning and archival preparation.
- 80–89%: throttle dispensable telemetry; protect core execution.
- 90–99%: critical conservation and no new bulk/synthetic load.
- At/above 100%: no unapproved high-volume jobs; prepare externally verified archive and controlled reduction. Never delete proof, financial records, auth material, or audit history without a verified recovery copy.

An initial Supabase guard in the private `imperial_control` schema adjusts only the CRM health-snapshot scheduler (5/15/30 minute schedule). This **does not** cap all database writes, avoid billing restrictions, or establish independent backups.

Handle `402` as billing/quota restriction; `429` as rate-limit; `401/403` as authorization/policy failures. Stop unnecessary retries and preserve incident evidence. All actual semantics depend on the provider.

## 3. Provider independence

- Separate canonical domain state from provider-specific implementations using adapters and explicit contracts.
- Preserve signed evidence of schema version, service configuration (without secrets), state export, job progress and license provenance.
- Maintain **two independent recovery locations** with restore tests before considering a backup complete. Do not store sensitive canonical data in public repositories.
- Keep portable source, dependency lockfiles, migration history, encrypted offsite backups and an annually reviewed disaster recovery plan.
- On provider disruption, freeze external writes and payouts, preserve an immutable incident ledger, report the actual affected service, and switch to an authorized provider only after verification.

## 4. Required proof gates

A release must produce a reviewable provider registry record with: provider, capability, tier, current rights/terms evidence date, scope, operator, permitted endpoints, credential class (not secret), budgets and rate limits, account owner, egress rules, fallback, backup location, recovery test, and signed release authorization.

Fail closed for unknown provider terms, ambiguous bundled quota rights, unavailable backup, lost key ownership, missing AI Passport, or external spending without approval.

## 5. Incident lessons

An account suspension for re-exposing a provider's bundled AI quota is a **provider-usage-policy** failure, not merely a storage quota failure. Safeguards must address both kinds of risks. The source scanner in this repository blocks the known high-risk `ValTownOpenAI` + hosted OpenAI-compatible relay combination; it is **not** a complete compliance certification or a substitute for source review.

**Current evidence boundary:** Supabase size exceeds the Free database quota. The quota guard throttles only nonessential snapshots; no offsite backup or data reduction is yet independently verified. Do not claim the risk resolved until the database is reduced and historical evidence is recoverable.
