---
name: apex-trigger-bypass-and-killswitch-patterns
description: "Runtime mechanisms to disable Apex triggers without commenting out code: Custom Metadata kill switches via Trigger_Setting__mdt, Custom Permission gates via FeatureManagement.checkPermission, Hierarchy Custom Settings, and TriggerControl static-state bypass for nested operations. NOT for recursive-trigger-prevention (use apex-recursive-trigger-prevention) — bypass disables a handler intentionally; recursion guards prevent the same handler from re-entering itself."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - apex
  - trigger
  - kill-switch
  - bypass
  - custom-metadata
  - feature-management
  - operational-excellence
triggers:
  - "how to disable trigger during data load"
  - "kill switch for apex trigger without deploying code"
  - "bypass triggers for integration user account"
  - "data loader bypassing validation rules and triggers"
  - "programmatic trigger bypass during cascade update"
  - "custom metadata flag to turn off apex handler"
inputs:
  - Trigger handler class(es) needing runtime control
  - Bypass scope (org-wide, per-user, per-profile, per-transaction)
  - Audit / governance requirements for bypass usage
  - Existing TriggerControl / Trigger_Setting__mdt deployment status
outputs:
  - Trigger_Setting__mdt records and Custom Permission scaffolding
  - TriggerHandler.run() override wired to TriggerControl.isActive
  - Programmatic bypass()/restore() pattern for nested DML
  - Audit log entry pattern when a bypass fires
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Apex Trigger Bypass And Killswitch Patterns

Activate when an Apex trigger needs to be disabled at runtime — for a data load,
a one-off support rerun, an integration user, or as a break-glass kill switch
during an incident — without commenting out code or hot-patching the org.
This skill is distinct from `apex-recursive-trigger-prevention`: recursion
prevention stops a handler from re-entering itself; bypass stops a handler
from running at all in a chosen scope.

## Why Bypasses Matter

- **Data loads and migrations.** Bulk inserts via Data Loader, ETL, or one-off
  scripts often need triggers off so denormalisation, rollups, and outbound
  callouts don't fire per row.
- **Integration users.** A nightly sync job from an external system has
  already validated and enriched data — the org's enrichment triggers should
  not re-run for that user.
- **Support reruns and backfills.** Replaying historical events should not
  refire side-effecting integrations.
- **Incident response (kill switch).** When a trigger is implicated in an
  outage, ops needs to disable it in seconds — without a deployment.

## Core Concepts

### 1. Custom Metadata kill switch (canonical)

`Trigger_Setting__mdt` records carry an `Is_Active__c` checkbox keyed by
`Object_API_Name__c` + `Handler_Class__c`. The repo's canonical `TriggerControl`
class (see `templates/apex/TriggerControl.cls`) reads this CMDT in a cached
SOQL on first call per transaction. Toggling `Is_Active__c` to `false` and
deploying the metadata change disables the handler org-wide. Custom Metadata
deploys faster than code and is auditable through the deployment record.

### 2. Custom Permission gate

`FeatureManagement.checkPermission('Bypass_Triggers')` is the canonical way to
ask "does the running user have the bypass capability?". The Custom Permission
is assigned via Permission Set, never directly to a profile. Integration users
get the perm set; admins do not (so accidental bypass during clicks is
impossible). The repo's `TriggerControl` already honours
`TriggerControl_BypassAll`.

### 3. Hierarchy Custom Setting toggle

A Hierarchy Custom Setting (`Trigger_Bypass__c` with checkbox fields per
handler) gives per-user, per-profile, and org-default override semantics.
Hierarchy lookups respect User → Profile → Org Default in that order. Useful
for short-lived overrides where a Permission Set assignment is too heavyweight,
but lacks the audit trail of Custom Metadata.

### 4. TriggerControl static-state bypass (in-transaction)

When Apex itself needs to suppress a downstream trigger during a cascade —
e.g. an Opportunity service that updates Accounts and does not want the
Account handler to re-derive territory — use programmatic
`TriggerControl.bypass('AccountTriggerHandler')` then `restore(...)` in a
`try/finally`. This is transaction-scoped static state; it does not survive
across transaction boundaries (Queueable, @future, Batch all start fresh).

### 5. Test guards

`Test.isRunningTest()` should NEVER short-circuit business logic. The right
pattern is to leave bypasses OFF in tests by default and have specific tests
opt in to the bypass via `TriggerControl.overrideForTest(...)`. Tests should
prove the trigger fires in the normal path.

## Why NEVER A Checkbox On User

Adding `Bypass_Triggers__c` to the `User` SObject sounds simple but is wrong:

- Users editing their own record can self-grant the bypass.
- There is no audit of who flipped the bit and when (User field history is
  limited and noisy).
- It cannot be assigned through Permission Set Groups, breaking least-privilege
  governance.
- It conflates identity (User) with capability (Permission), an
  anti-pattern called out in Salesforce Well-Architected Security guidance.

Use a Custom Permission and assign it through a Permission Set instead.

## Governance — Every Bypass Must Be Auditable

Every code path that decides to bypass should write a single line to an
`Application_Log__c` (or platform event) — "skipped AccountTriggerHandler at
2026-04-28T14:02:11Z because TriggerControl_BypassAll permission is granted
to user 005...". Without this, post-incident forensics is impossible.

## Test Pattern

ALWAYS run trigger tests with no bypass applied unless the test is explicitly
proving the bypass works. Do this by clearing static state in
`@TestSetup` and asserting `TriggerControl.isActive(...) == true` before
the work.

## Recommended Workflow

1. Decide bypass scope: org-wide kill switch (CMDT), per-user/integration
   (Custom Permission), per-profile or short-lived (Hierarchy CS), or
   in-transaction cascade suppression (programmatic).
2. Add or update the `Trigger_Setting__mdt` record (or Custom Permission
   assignment) — never edit the trigger code.
3. Wire the handler's `run()` entry point to call
   `TriggerControl.isActive(sObjectName, handlerName)` and short-circuit.
4. For programmatic bypass during a cascade, wrap the inner DML in
   `try { TriggerControl.bypass(...); ... } finally { TriggerControl.restore(...); }`.
5. Emit an `Application_Log__c` entry whenever a bypass actually fires.
6. Write tests that prove (a) the trigger runs by default, (b) the kill
   switch disables it, and (c) restore() reverts the static-state bypass.
7. Document the kill-switch runbook entry — who can flip it, how to flip it,
   how to verify, how to revert.

## Review Checklist

- [ ] Handler `run()` calls `TriggerControl.isActive(...)` first
- [ ] Custom Permission is `FeatureManagement.checkPermission`-gated, not a User field
- [ ] `Trigger_Setting__mdt` record exists for every handler
- [ ] Programmatic bypass uses `try/finally` to guarantee restore
- [ ] Bypass invocations write to `Application_Log__c`
- [ ] Tests run with bypass OFF by default
- [ ] No commented-out trigger code anywhere
- [ ] Runbook documents how to flip the kill switch and revert

## Salesforce-Specific Gotchas

1. **CMDT cache lag.** `Trigger_Setting__mdt` changes can take a few seconds
   to propagate after deploy because of platform-side metadata caching.
   Verify by hitting the handler from a fresh transaction.
2. **Static state dies at transaction boundaries.** A Queueable enqueued from
   inside `TriggerControl.bypass(...)` runs in a NEW transaction with fresh
   static state — bypass is gone.
3. **Hierarchy CS lookup order is User → Profile → Org Default.** Setting
   only the org default leaves admin-test users bypassed unintentionally.

## Output Artifacts

| Artifact | Description |
|---|---|
| `Trigger_Setting__mdt` records | Per-handler kill switch toggles |
| `TriggerHandler.run()` override | Calls `TriggerControl.isActive(...)` first |
| Programmatic bypass blocks | `try/finally` wrappers around cascade DML |
| Bypass audit log entries | `Application_Log__c` rows on each bypass fire |
| Kill-switch runbook entry | Ops doc for incident response |

## Related Skills

- `apex/apex-recursive-trigger-prevention` — re-entry guards (different problem)
- `apex/apex-trigger-handler-framework` — the handler pattern being gated
- `apex/apex-application-logger` — the audit log destination
