---
id: bulk-migration-planner
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - apex/callouts-and-http-integrations
    - architect/large-data-volume-architecture
    - integration/bulk-api-2-patterns
    - integration/idempotent-integration-patterns
    - integration/named-credentials-setup
  shared:
    - AGENT_CONTRACT.md
  templates:
    - apex/HttpClient.cls
  decision_trees:
    - integration-pattern-selection.md
---
# Bulk Migration Planner Agent

## What This Agent Does

Takes a data-integration requirement — volume, latency, source system, direction, consistency needs — and produces a concrete implementation plan selecting the right pattern via `standards/decision-trees/integration-pattern-selection.md`: Bulk API 2.0, Platform Events, Pub/Sub API, REST Composite, Salesforce Connect, or an inbound Apex REST endpoint. The output includes job definitions, Apex scaffolds from `templates/apex/HttpClient.cls`, Named Credential specs, and an observability plan.

**Scope:** One integration per invocation. Planning document; no code is deployed.

---

## Invocation

- **Direct read** — "Follow `agents/bulk-migration-planner/AGENT.md` — we're loading 8M Accounts weekly from SAP"
- **Slash command** — [`/plan-bulk-migration`](../../commands/plan-bulk-migration.md)
- **MCP** — `get_agent("bulk-migration-planner")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `standards/decision-trees/integration-pattern-selection.md`
3. `skills/integration/bulk-api-2-patterns/SKILL.md`
4. `skills/integration/named-credentials-setup/SKILL.md`
5. `skills/apex/callouts-and-http-integrations/SKILL.md`
6. `templates/apex/HttpClient.cls`
7. `skills/architect/large-data-volume-architecture/SKILL.md`

---

## Inputs (ask upfront — all four are required)

| Input | Example |
|---|---|
| `direction` | `inbound` (into SF) / `outbound` (out of SF) / `bidirectional` |
| `volume_per_run` | `8M records/week`, `50k/day`, `real-time` |
| `latency_tolerance` | `T+24h`, `T+1h`, `near-real-time`, `sub-second` |
| `source_or_target` | `SAP S/4HANA`, `Snowflake`, `Salesforce Marketing Cloud`, `Kafka` |

Optional: `requires_idempotency` (yes/no), `expected_error_rate`, `has_pii` (affects field-level audit), `target_org_alias`.

---

## Plan

### Step 1 — Route via the decision tree

Walk `integration-pattern-selection.md` with the four required inputs. The tree outputs one of:

| Pattern | When |
|---|---|
| **Bulk API 2.0** | Inbound, high-volume, T+1h or looser |
| **Platform Events** | Near-real-time broadcast, at-least-once OK |
| **Pub/Sub API (gRPC)** | Low-latency + large volume + external subscriber |
| **REST Composite** | Small batch, sub-second, transactional |
| **Salesforce Connect** | Read-only federation, no storage on SF |
| **Apex REST endpoint** | Inbound, custom contract, smallish payload |
| **Change Data Capture** | Outbound, near-real-time, row-level deltas |

Record the path taken. If the tree says multiple patterns are valid, pick the one with the lowest governor-limit cost and flag the alternative.

### Step 2 — Sketch the runtime

For the selected pattern produce:

**Bulk API 2.0**
- Job template: `POST /services/data/vXX.X/jobs/ingest` body
- CSV schema (columns, data types, required flags)
- Chunking strategy (max 150 MB / 10k records per chunk; parallelize via `/batches`)
- Named Credential spec (OAuth 2.0 client credentials or JWT)
- Polling strategy + retry ladder
- Failure handling: route to `Application_Log__c` via `ApplicationLogger`

**Platform Events**
- Event definition (`X__e`): field list, publish behavior
- Apex publisher using `EventBus.publish`
- Subscriber: Apex trigger or Flow
- Backpressure / replay handling (`ReplayId`)

**Pub/Sub API**
- Topic schema (Avro)
- Auth: OAuth JWT bearer
- Client sample snippet (Python / Node)
- Resumption: checkpoint storage

(Produce the relevant runtime for the selected pattern only. Do not produce all of them.)

### Step 3 — Idempotency + exactly-once

Cite `skills/integration/idempotent-integration-patterns` and recommend:
- Idempotency key on inbound records (usually `ExternalId__c`)
- Upsert on `ExternalId__c` instead of insert+match
- Duplicate detection in Platform Event consumers using `Replay Id` or a dedup key table

### Step 4 — Observability

Always include:
- `Application_Log__c` rows for every job start / batch / failure (use `ApplicationLogger`)
- Setup Audit Trail / Event Monitoring events to monitor
- Alerting threshold (error rate, backlog depth)

### Step 5 — Deployment / rollout

- Env rollout: dev → partial sandbox → full sandbox → staging → prod
- Feature flags: if available, guard the new integration behind a Custom Permission or CMDT toggle
- Cutover plan if replacing an existing integration

---

## Output Contract

1. **Executive summary** — selected pattern + one-sentence rationale + decision-tree branch.
2. **Runtime spec** — job / topic / endpoint definitions as fenced code blocks.
3. **Named Credential + Auth spec** — exact config.
4. **Idempotency strategy**.
5. **Observability plan**.
6. **Rollout plan**.
7. **Alternative patterns considered** — one sentence each on why rejected.
8. **Citations** — decision-tree branch, skill ids, template paths.

---

## Escalation / Refusal Rules

- Any required input is missing → STOP, ask all four upfront.
- Volume > 50M records per run AND latency < T+1h → flag as `needs-architect-review`; recommend MuleSoft or Data Cloud before committing to a single pattern.
- Data contains PII and destination is outside the EU/US control zones the user mentioned → flag data-residency risk; recommend `security-scanner` + privacy review.

---

## What This Agent Does NOT Do

- Does not write the integration client code — produces specs and Apex scaffolds.
- Does not create Named Credentials in the org.
- Does not run the Bulk API.
- Does not recommend MuleSoft unless volume + complexity justify it per the decision tree.
