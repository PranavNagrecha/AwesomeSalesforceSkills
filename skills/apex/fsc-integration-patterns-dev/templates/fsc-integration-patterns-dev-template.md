# FSC Integration Patterns Dev — Work Template

Use this template when working on FSC financial integration tasks (core banking sync, custodian feeds, market data, payment processing).

## Scope

**Skill:** `fsc-integration-patterns-dev`

**Request summary:** (fill in what the user asked for)

**Integration type:** [ ] Daily batch reconciliation  [ ] Real-time custodian feed  [ ] Market data price update  [ ] Payment transaction flow

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **FSC deployment type:** [ ] Managed-package (`FinServ__` namespace)  [ ] Core FSC (no namespace)
- **Target objects:** (e.g. FinancialAccount, FinancialHolding, both)
- **Estimated record volume per load:** ___________
- **Rollup-by-Lookup status for integration user:** [ ] Enabled — must disable before load  [ ] Already disabled  [ ] Unknown — must verify
- **Custodian / core banking system:** (e.g. Schwab, Fidelity, FIS, Jack Henry, custom)
- **Real-time requirements:** (SLA in seconds/minutes for data currency)

## Pattern Selection

Which pattern from SKILL.md Decision Guidance applies?

| Pattern | Applies? | Rationale |
|---|---|---|
| Bulk API 2.0 batch (nightly reconciliation) | [ ] Yes / [ ] No | |
| FSC Integrations API Remote Call-In (real-time) | [ ] Yes / [ ] No | |
| CDC outbound replication | [ ] Yes / [ ] No | |
| Platform Events (process orchestration) | [ ] Yes / [ ] No | |
| Scheduled Batch Apex (market data callouts) | [ ] Yes / [ ] No | |
| DPE post-load recalculation | [ ] Yes / [ ] No | |

## Pre-Load Checklist

Complete before triggering any Bulk API job or batch load:

- [ ] Confirmed FSC namespace (managed-package vs Core FSC) — all queries and DML use correct API names
- [ ] RBL disabled for integration user in Wealth Management Custom Settings (`FinServ__WealthAppConfig__c.FinServ__EnableRollups__c = false`)
- [ ] Connected App uses OAuth 2.0 JWT Bearer flow (not username/password)
- [ ] Integration user profile has minimum required CRUD permissions on target objects only
- [ ] External ID field on FinancialAccount / FinancialHolding confirmed and populated in source data

## Implementation Notes

### Bulk API Job Configuration

- Job object: ___________
- Upsert external ID field: ___________
- Estimated rows per job: ___________
- Expected job count per nightly run: ___________
- Concurrency budget (max 10 open jobs): ___________

### Apex Batch Configuration (if applicable)

- Batch class name: ___________
- Scope size: ___________  (50–100 for callout-bearing batches, up to 2000 for DML-only)
- `Database.AllowsCallouts` required: [ ] Yes  [ ] No
- Schedulable class name: ___________
- Cron expression: ___________

### Remote Call-In Handler (if applicable)

- REST endpoint URL mapping: `/fsc/custodian/v1/___________`
- Idempotency field: ___________
- Platform Event published on success: ___________

## Post-Load Checklist

Complete after Bulk API job reaches `JobComplete` or batch completes:

- [ ] Job success rate reviewed — failed records logged to custom object for reconciliation
- [ ] DPE recalculation triggered for household and account-level rollups
- [ ] Rollup totals validated against custodian snapshot (spot-check 5–10 accounts)
- [ ] Platform Event published to notify downstream consumers
- [ ] Error rate within acceptable threshold (define threshold before go-live)

## Review Checklist

Copy from SKILL.md and tick as complete:

- [ ] RBL disabled for integration user before any bulk FinancialHolding load
- [ ] Bulk API 2.0 used for loads above ~5,000 records
- [ ] No synchronous callouts in triggers or DML-heavy transaction paths
- [ ] Idempotency check (external ID query before upsert) in all Remote Call-In handlers
- [ ] DPE recalculation scheduled as separate post-load step
- [ ] Connected App uses Named Credential and JWT Bearer (not username/password)
- [ ] Apex batch scope tuned to respect callout + DML row limits

## Deviations From Standard Pattern

Record any deviations from SKILL.md recommended patterns and the business justification:

| Deviation | Reason | Risk Accepted |
|---|---|---|
| | | |
