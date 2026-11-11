# IMPERIAL Core — Operations Guard Pack v0.1

**Architect:** Alexander Nikolaevich Romaskevich (RomaskevicH), Founder • Owner • CEO • Chief Systems Architect  
**Date:** 2026-11-10  
**Status:** runnable OFFLINE source proposals, not cloud plugins or a deployed agent  
**Budget:** FREE_ONLY / USD 0  

## Verified problem statement

On 10 November 2026, read-only provider records showed repeated 512 MiB Render OOM kills for GOD'S EYE deployments. Supabase reported zero active NCA model processes, an expired controlled-worker permit, zero live CRM workers and zero active jobs. HEALTHY or QA_PASS in a laboratory subsystem must not be interpreted as production readiness.

## Three modules, no duplicate platform

| Guard | Python function | Bounded checks | Never does |
|---|---|---|---|
| Render Resource Guard | assess_render_events | OOM patterns, missing/stale observations, no false current-health assertions | restart/scale/billing |
| NCA Mission Truth Gate | assess_nca_readiness | expired approvals, zero runtime, stale QA, gate and kill-switch conflicts | issue approval, dispatch agent, certify production |
| Camera Rights Preflight | preflight_camera_source | closed metadata schema, rights reference, expiry, permitted purposes/events, retention | connect cameras, verify rights, face search, authorize streams |

All functions are deterministic, standard-library-only and have no network access. Their inputs are untrusted observations, not signed attestation. A passing preflight still requires a separately verified Owner permit and independent QA. Never publish credentials, camera IP addresses, private network topology, video or customer data.

## Run the tests locally

    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_operational_guards.py' -v
    PYTHONPATH=src python3 -m unittest discover -s tests -v

Existing Security Kernel CI discovers all tests on a pull request, subject to the user's normal GitHub Actions budget and permissions. Passing tests are local/CI software checks, not cloud deployment or independent security certification.

## Run the offline JSON CLI

Render synthetic fixture:

    printf '%s\n' '[{"timestamp":"2026-11-10T10:00:00Z","type":"server_failed","details":{"reason":{"oomKilled":{"memoryLimit":"512Mi"}}}}]' | PYTHONPATH=src python3 tools/ops_guard.py --kind render --service-id srv-demo --now 2026-11-10T10:30:00Z

The result is OOM_OBSERVED and recovery_authorized=false. Two or more OOM kills yield REPEATED_OOM even if a later event says server_available.

Prepare sanitized, local JSON for the other two commands, never storing source data in GitHub:

    PYTHONPATH=src python3 tools/ops_guard.py --kind nca --now 2026-11-10T10:30:00Z < sanitized-nca.json
    PYTHONPATH=src python3 tools/ops_guard.py --kind camera --now 2026-11-10T10:30:00Z < synthetic-camera-descriptor.json

NCA input must have four sections: nca, worker, crm, gate. An expired permit and zero model processes produce BLOCKED_OR_LAB_ONLY. Even a self-reported all-green snapshot yields EXTERNAL_VERIFICATION_REQUIRED and execution_authorized=false.

Camera input must have exactly source_id, tenant_id, source_type, rights_reference, expires_at, purpose, event_types and retention_seconds; it contains no camera URL. An unknown source, unapproved event, URL/credential field, expired right or metadata archive above its scope is denied. Eligible sources are only eligible_for_external_review; stream_connection_authorized is always false.

The CLI accepts at most 128 KiB from standard input and makes no HTTP calls.

## Work packages — sequentially

1. Authorized private read-only collector prepares redacted snapshots from Render and Supabase under existing provider quotas. Never connect API credentials to the public source.
2. Investigate Render OOM with memory profiling, dependency and deployment inventory, allowlist egress and free-tier resource limits. No auto restart or plan change.
3. Restore one real NCA worker only after the Owner's cryptographic permit, verified AI Passport, Guardian Core, Approval Gateway and kill switch. Collect independent model-process and QA evidence; never automatically extend expired permission.
4. Extend existing CYBER HAK IMPERIAL EYE after a private authorized source license/rights review, using synthetic or operator-approved video. Never perform universal person tracking, biometric search or unauthorized camera discovery.
5. Finish CONSTRUCTOR AI's independent app generation and Docker acceptance; connect ProofGraph to reproducible release evidence.

Canonical governance: Architect -> HANTER -> Federated Orchestrators -> Nano Core Agents -> Execution, with Enterprise Skills, ProofGraph, Audit Ledger, Zero Trust, Owner Kill Switch, Public/Private Boundary and CRYPTO IMPERIAL Ecosystem Boundary. CRYPTO IMPERIAL is never implicitly accessible to the plugin suite.

These are **three offline source plugins plus a CLI**, not installed ChatGPT plugins, remotely running agents or completed incident remediation.

**Architecture Before Implementation. Evidence Before PASS.**
