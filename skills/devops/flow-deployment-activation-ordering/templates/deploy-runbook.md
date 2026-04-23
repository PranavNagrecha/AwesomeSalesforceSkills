# Flow Deploy Runbook

## Scope

- Target org:
- Flows changing:
- Subflows affected:
- Apex callers affected:

## Pre-Deploy Inventory

| Flow | Current active version | Paused interviews | Scheduled runs |
|---|---|---|---|
|   |   |   |   |

## Activation Mode

- [ ] Deploy active (auto)
- [ ] Deploy inactive, activate after smoke test

Rationale:

## Order

1. Subflows: 
2. Callers: 
3. Scheduled flows: 

## Smoke Tests

- [ ] Run each changed flow from Setup with a known record.
- [ ] Run Apex invoker tests.

## Rollback

- Pre-deploy active versions captured? Y / N
- Rollback command (pointer flip):

## Post-Deploy Verification

- [ ] Active version matches expectation.
- [ ] No Flow error emails for 1h.
- [ ] Paused-interview resume for N hours observed.

## Sign-Off

- [ ] Pre-deploy inventory captured.
- [ ] Subflows deployed before callers.
- [ ] Rollback is pointer flip, not redeploy.
- [ ] Retention respects paused-interview lifetimes.
