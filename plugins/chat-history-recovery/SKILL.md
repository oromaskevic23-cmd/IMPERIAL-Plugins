# IMPERIAL Chat History Recovery — Ten Specialized Search Agents

**Plugin:** `imperial.chat-history-recovery` v0.1.0  
**Founding architect:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder · Owner · CEO · Chief Systems Architect of IMPERIAL Core.  
**Status:** executable offline source reference, tested on synthetic data. NOT a ChatGPT account connector, enterprise production service, or 10 deployed LLM agents.

## Mission

Rapidly recover exact original decisions, modules, technical documents and chronological checkpoints from past ChatGPT conversations, particularly **before the Val Town period**. The user supplies the source export. Every result references a concrete `chatgpt-export:<conversation-id>/<message-id>`, includes title, UTC timestamp, branch status, redacted excerpt and SHA-256 digest. A citation here is an **export locator**, not an automatically resolvable web URL.

## Ten bounded search roles

| NCA role | Domain |
| --- | --- |
| NCA-REC-01 | Canonical architecture |
| NCA-REC-02 | Module and repository names |
| NCA-REC-03 | Documents and specifications |
| NCA-REC-04 | Decisions and directives |
| NCA-REC-05 | Timeline and checkpoints |
| NCA-REC-06 | HANTER / ASTRA / ORION / NCA orchestration |
| NCA-REC-07 | Providers, servers and Val Town |
| NCA-REC-08 | Security, AI Passport, Guardian Core |
| NCA-REC-09 | Engineering, VELION and CONSTRUCTOR AI |
| NCA-REC-10 | Recovery, incidents and backups |

**Implementation truth:** Ten deterministic ranking passes share a local SQLite FTS5 corpus. These are role-based **search simulators**, not ten network-connected autonomous AI workers. No LLM prompt, private account API or production permission is created.

## Prepare an eligible personal ChatGPT data export

ChatGPT on iOS: **Settings → Data controls → Export data**, then follow the confirmation. Download the archive from the email/SMS provided by the platform and extract it locally. Read OpenAI's official data export instructions: https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data

Look for `conversations.json` or numbered `conversations-*.json` files. The importer reads **one JSON array per command**; use a separate new database per source file. Export formats can change. It indexes textual `user` and `assistant` messages only. Images, connected apps, deleted chats, metadata files and binary artifacts are not reconstructed. ChatGPT export data can contain private information: **never commit your export to GitHub or share it publicly**.

## Run locally (Python 3.11+, standard library only)

The user must provide the export deliberately and run this on a **trusted machine**.

```sh
PYTHONPATH=src python tools/chat_history_recovery.py index \
  --export /private/path/conversations.json \
  --database /private/path/chat-history-redacted.sqlite

PYTHONPATH=src python tools/chat_history_recovery.py search \
  --database /private/path/chat-history-redacted.sqlite \
  --query "HANTER CONSTRUCTOR AI" --before-val-town --limit 10
```

The `--before-val-town` option uses the **first textual user mention** of "Val Town" or `val.run` in the exported data as a heuristic checkpoint; this does NOT prove the platform's real first use or actual migration date. Review that value before relying on it. For a dated owner-confirmed cutoff, use:

```sh
PYTHONPATH=src python tools/chat_history_recovery.py search \
  --database /private/path/chat-history-redacted.sqlite \
  --query "VELION" --before 2026-08-01 --limit 10
```

**This date is only an illustrative CLI example, NOT a claim that Val Town started on 1 August 2026.** All date boundaries use UTC midnight and are exclusive. By default alternate regenerated response branches are suppressed; use `--include-alternates` to inspect them, and treat those as **noncanonical prior variants**, not final approved instructions.

## Security and evidence boundaries

- **Read-only source:** no network calls, no reading ChatGPT through a live session, no credentials, no model execution, no remote orchestration.
- **Local index:** SQLite is stored on disk with owner-only POSIX file permissions and basic regex redaction of common private keys, bot tokens, JWTs, PATs and email addresses. **It is NOT encrypted; redaction is incomplete by nature.** Use an encrypted owner-controlled disk, do not place it in a shared/cloud-synced folder, and securely delete it when no longer needed.
- **Fail closed:** reject input symlinks, overwrite attempts, oversized/invalid JSON, unsupported query dates, and unverifiable timestamps. The output has exact source IDs and a sanitized SHA-256 digest; digests are byte consistency checks, not independent evidence of authorship.
- **Data interpretation:** old AI replies may contain incorrect claims; discovery is not factual validation. Verify significant findings against actual GitHub commits, server logs and independent artifacts.
- **No false citations:** exported local message IDs are distinct from live ChatGPT links. Never invent a file download link or a source line that was not indexed.
- **Governance:** HANTER → federated domain orchestrators → Search NCA; preserve AI Passport, Enterprise Skills, Guardian Core, Approval Gateway, ProofGraph, Audit Ledger, Zero Trust, Public/Private Boundary, CRYPTO IMPERIAL Ecosystem Boundary and Owner Kill Switch. FREE_ONLY until separate authorization.

## Target development programme — 6 to 8 weeks

Programme starts **2 November 2026** and targets **14–28 December 2026**. This is a planning target, **not** autonomous background delivery.

1. **Weeks 1–2:** v0.1 offline export importer, branch-aware 10-role search, temporal filter, structured evidence, negative privacy tests — **implemented in this PR**.
2. **Weeks 3–4:** owner-controlled local secure storage, explicit consent and access policy, multi-export deduplication, supported file/document provenance and better exact-match diagnostics.
3. **Weeks 5–6:** real authorized integration into HANTER with per-agent AI Passport, Guardian Core, tenant separation, active work approval and external independent QA.
4. **Weeks 7–8:** independent recall/precision benchmarks, source-coverage reports, incident recovery exercises, rollback and a separately authorized private deployment.

Future work is **not marked complete** until separately implemented and verified. If no Owner export is supplied, this plugin cannot reconstruct the requested history from ChatGPT automatically. A persistent production worker is not part of v0.1.

## Source

- [Python search engine](../../src/imperial_plugins/chat_recovery.py)
- [Local CLI](../../tools/chat_history_recovery.py)
- [Negative test suite](../../tests/test_chat_recovery.py)
- [Source manifest](../../manifests/chat-history-recovery.json)
- [GitHub Actions test workflow](../../.github/workflows/chat-history-recovery-ci.yml)

No third-party source was copied or relicensed. Original work only is attributed to IMPERIAL Core project contributors under the founding architecture of Alexander Nikolaevich Romaskevich (RomaskevicH).
