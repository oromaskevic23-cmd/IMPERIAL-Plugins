# Security policy

**Do not submit passwords, tokens, private keys, PII, production workflows or unpublished IMPERIAL Core source code.**

Security reports: use the GitHub repository's private vulnerability reporting feature where enabled; otherwise contact the repository owner through a private channel. Never post exploitable details in public issues.

Current implementation is experimental. Default kill switch is engaged, no network or arbitrary plugin execution is present, and signing helpers are for trusted issuers only. HMAC demonstrates authentication inside one secret-sharing trust domain; it does **not** establish non-repudiation or Ed25519 identity. SQLite hash-chain verification detects casual changes but is not administrator-proof or WORM storage. External secure key custody, secret rotation, signed releases, isolation, tenant isolation, rate limiting, branch rules and external attestation are future production gates.

If a production incident is suspected: engage the Owner Kill Switch; revoke signing keys in the private runtime; isolate NCA and orchestrator credentials; preserve evidence and rotate affected secrets.
