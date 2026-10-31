# Federated Plugin Architecture

```text
Architect (final architectural authority)
  | Owner Kill Switch / IntentLock
HANTER (command center: intake, policy, evidence)
  | Approval Gateway + Guardian Core + AI Passport
  +-- Federated Orchestrator A (e.g. ASTRA)
  |     +-- Team / NCA / sub-NCA
  +-- Federated Orchestrator B
        +-- Team / NCA / sub-NCA
                    |
            Enterprise Skills + Plugin interface
                    |
            Audit Ledger + ProofGraph evidence
```

**No single global execution orchestrator**. HANTER coordinates routing and authorization boundaries, not unbounded code execution. ORION is an intelligence component. Each Runtime Domain and tenant must retain separate secrets, quotas, policy and state.

## Public / Private Boundary

Public: declarative interfaces, test vectors, examples, documentation, independent unit tests. Private: runtime credentials, actual signing keys, customer records, payout destinations, protected orchestrator instructions, commercial agreements, private source.

## CRYPTO IMPERIAL Ecosystem Boundary

No plugin may transfer funds, manage wallets, promise token prices, issue a token or declare PAYMENT_CONFIRMED without separately authorized and externally evidenced actions. IMPERIUM is a **long-term architectural concept** for a potential digital currency for AI agents worldwide, not an assertion of current universal usage or market status.

## Execution pipeline (target)

IntentLock → identify task → validate signed AI Passport → resolve tenant/orchestrator → validate manifest and capabilities → Guardian decision → Owner Approval Gateway for non-read actions → sandboxed worker → independent QA → ProofGraph → Audit Ledger → evidence-backed status.

The code here implements only local checks and SQLite evidence. It does not implement sandboxing, actual NCA workers or federated remote dispatch.
