---
name: code-review-checklist-salesforce
description: "Structured Salesforce code review for Apex, triggers, async, and tests before merge or deployment — governor limits, bulk-safe triggers, CRUD/FLS and sharing posture, meaningful tests, and naming consistency. NOT for AppExchange security-review-only deep dives — use security/secure-coding-review-checklist."
category: devops
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "peer review Apex trigger before production deployment"
  - "Salesforce code review checklist for governor limits and bulkification"
  - "verify our Apex handles two hundred records without SOQL in loops"
  - "review this pull request of Apex classes before we merge it"
  - "check whether bumping a class to API 67.0 changes its sharing behaviour"
  - "flag WITH SECURITY_ENFORCED and missing sharing keywords in a code review"
tags:
  - code-review-checklist-salesforce
  - code-review
  - apex
  - governor-limits
  - bulkification
  - crud-fls
  - unit-tests
  - devops
  - pull-request
inputs:
  - "Diff or full source for Apex classes, triggers, batch/queueable/scheduled code under review"
  - "Whether the change is subscriber org, ISV package, or single-org custom code"
  - "Target transaction context (synchronous trigger, async job, REST, Aura/LWC controller)"
outputs:
  - "Section-by-section review notes tied to this checklist"
  - "List of blocking vs advisory findings for the PR or release record"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Code Review Checklist Salesforce

This skill activates when a team needs a repeatable, platform-grounded review of Salesforce custom code before merging or promoting a release. It complements CI by giving human reviewers (or an agent) a single pass through the categories that most often cause production regressions or deployment failures: bulk safety and governor consumption, data access enforcement, test quality, and consistency with Salesforce naming and structure guidance.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the execution entry points (trigger on `Account`, `@AuraEnabled` method, REST, batch `execute`, etc.) and the maximum batch size they must support (200 for synchronous trigger contexts).
- Confirm sharing intent: `with sharing`, `without sharing`, `inherited sharing`, and the query-level access mode (`WITH USER_MODE` / `WITH SYSTEM_MODE`) — mismatches here are data leaks, not style issues. The correct idiom is gated on the class's own `apiVersion` in its `.cls-meta.xml`, not on the org's release; see [Apex security idiom by API version](../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version).
- Pull the latest local test run or CI output so coverage numbers are not mistaken for assertion quality.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which `apiVersion` does each changed `.cls-meta.xml` / `.trigger-meta.xml` carry, and did the diff change it? | At 67.0 the default access mode becomes user mode and undeclared classes run `with sharing`; a version bump alone changes behaviour (gotcha 4). | The reviewer knows which default applies per file and treats a version bump as a behaviour change, not a no-op. |
| What is the largest batch each entry point receives (UI save, Data Loader, Bulk API, integration)? | Triggers receive chunks of up to 200 records; code proven on five rows fails at 200 (gotcha 6). | A concrete row count for the bulk test the reviewer will demand. |
| Is partial success (`allOrNone=false`) a product requirement for this DML? | Partial success returns per-row results the caller must inspect, or failures vanish (gotcha 1). | Either all-or-nothing DML, or a named owner for the failed-row handling. |
| Which profile or permission set runs this code in production? | Tests run as an admin hide FLS and sharing failures (gotcha 2). | The persona to use in `System.runAs`, and the field list that must be readable. |
| Does any class need to see records the running user cannot? | `without sharing` / `WITH SYSTEM_MODE` must be justified per method, and on 67.0 a trigger body query is user mode unless it says otherwise (gotcha 5). | A documented elevation scope the reviewer can check against the threat model. |
| Will this change enqueue jobs from loops, `finish`, or other queueables? | Chained queueables have a stack-depth limit and `System.enqueueJob` has a per-transaction cap (gotcha 3). | A bounded fan-out design and an expected job count per upstream event. |
| Are scheduled or batch jobs running against classes this PR changes? | By default an Apex class with active jobs cannot be redeployed (gotcha 7). | A deploy-window plan: pause the jobs, or confirm the Deployment Settings option that allows deploys with jobs. |

A proper review adds an explicit, version-aware access-mode decision and a bulk test sized to the real entry point, where "just reading the diff" approves code that passes on five admin-owned rows and fails on the first full batch.

---

## Core Concepts

### Governor limits and bulk safety

Salesforce enforces per-transaction limits on SOQL, DML, heap, CPU, and callouts (100 SOQL queries synchronous / 200 asynchronous; 150 DML statements). Code that issues queries or DML inside a loop over trigger records scales linearly with batch size and fails at 200. The review goal is constant work per transaction: collect ids, query once, map results, update collections. Async jobs get their own, larger limit scope; still avoid unbounded queries inside loops because heap and CPU compound.

### CRUD, FLS, and sharing

Reading or writing data without respecting the running user’s permissions is both a security defect and a deployment risk. Prefer `WITH USER_MODE` on inline SOQL, and `Security.stripInaccessible(AccessType, records).getRecords()` when returning dynamic query rows to callers — user mode raises a `QueryException` (inspect it with `getInaccessibleFields()`) and fails the operation, while `stripInaccessible` drops the inaccessible fields and continues, so the choice is about whether silent partial success is acceptable.

`WITH SECURITY_ENFORCED` is **not** an option a reviewer accepts. The Apex Developer Guide's versioned behaviour changes state that in API version 67.0 and later you can't use the `WITH SECURITY_ENFORCED` clause in SOQL SELECT queries in Apex code. On a 67.0+ class its presence is a compile failure, not a style note; on older classes it is tech debt with a named migration to `WITH USER_MODE`.

### Version-gated defaults

The controlling fact is the `apiVersion` in the class's own `.cls-meta.xml`, not the org's release — a Summer '26 org runs a class pinned to 58.0 with the older behaviour. Two defaults flip at 67.0: database operations run in user mode unless system mode is set explicitly, and classes with no sharing declaration run `with sharing`. At 66.0 and earlier, system mode is the default and an undeclared class takes its sharing from the inheritance chain or caller. The canonical per-version table is [Apex security idiom by API version](../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version); cite it rather than restating it here.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- AccountService.cls-meta.xml: this number, not the org release, decides the access-mode default -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

### Tests as contract, not decoration

The 75% coverage gate is a floor; the Apex Developer Guide itself says not to focus on the percentage. Reviewers insist on assertions that prove behaviour, `@testSetup` for shared data, and negative paths (expected exceptions, bulk scenarios). Tests that only instantiate classes to raise line coverage hide regressions until production.

### Naming and structure

The Apex Developer Guide recommends Java naming standards: classes start with a capital letter, methods with a lowercase verb, and variables have meaningful names. Suffixes such as `AccountTrigger` / `AccountTriggerHandler` / `AccountService_Test` are a team convention layered on top, not platform guidance — the review enforces whichever convention the team wrote down.

### Architectural compliance

When more than one trigger is defined on an object for the same event, the platform does not guarantee their execution order. That is the platform fact behind the common practice of one trigger per object with the logic in a handler class: the handler can be tested in isolation, ordering is explicit in code, and two developers stop colliding on the same trigger file. Reviewers flag any logic-bearing trigger body (branching, SOQL, DML, service calls) as a blocking architectural issue under this team practice.

---

## Common Patterns

### Bulkified trigger handler

**When to use:** Any `before` or `after` trigger that touches related records.

**How it works:** Loop `Trigger.new` once to collect keys; run one SOQL per object type; build maps; second loop applies updates to collections; single DML per type outside inner queries.

**Why not the alternative:** Querying inside `for (SObject row : Trigger.new)` produces N+1 SOQL and fails under load.

### USER_MODE for user-facing reads

**When to use:** Inline SOQL in services called from Lightning or Experience Cloud where the running user’s FLS must apply.

**How it works:** Append `WITH USER_MODE` to the SOQL; invalid field access throws instead of leaking data. On a 67.0+ class user mode is already the default, but writing it out keeps the intent visible when the code is copied into an older-version class.

**Why not the alternative:** Manual describe checks drift when fields are added; dynamic SOQL without stripping is easy to get wrong.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Trigger loads related records | Collect ids, one query, map-driven updates | Keeps SOQL count flat vs batch size |
| Dynamic SOQL from controlled inputs | Bind variables and `String.escapeSingleQuotes` where binds are impossible | Reduces injection and accidental full-table scans |
| DML on mixed SObject lists | `Database.insert(records, false)` only when partial success is a product requirement | All-or-nothing default is usually safer for data integrity |
| Test needs shared expensive data | `@testSetup` once per class | Cuts CPU and avoids order-dependent tests |
| Method only used in system batch | Document `without sharing` rationale in class header | Reviewers flag implicit sharing without comment |
| Diff bumps `apiVersion` from 66.0 or lower to 67.0 or higher | Treat as a behaviour change: re-run permission-sensitive tests as the production persona | User-mode and `with sharing` defaults apply from 67.0 |

---

## Recommended Workflow

1. Map entry points and data flows from the diff; record each changed file's `apiVersion` from its `-meta.xml` and note the transaction context (synchronous trigger, async job, REST controller).
2. Run `python3 skills/devops/code-review-checklist-salesforce/scripts/check_code_review_checklist_salesforce.py --manifest-dir force-app` over the changed package directory; treat its ERRORs (`WITH SECURITY_ENFORCED` on a 67.0+ class) as blocking and its WARNs as review prompts.
3. Walk the governor and bulk section by hand: SOQL/DML/callouts per loop, collection sizes, queries against large objects; every synchronous trigger path must tolerate 200 records without per-row queries or DML.
4. Verify CRUD/FLS and sharing: explicit `with sharing` / `without sharing` / `inherited sharing` on every class with database operations; `WITH USER_MODE` or `Security.stripInaccessible` for user-facing reads; a written reason for every `WITH SYSTEM_MODE` and `without sharing`.
5. Read the test classes: assertions with messages, a 200-row bulk method, negative paths, `System.runAs` as the production persona; no `SeeAllData=true` where `Test.getStandardPricebookId()` or created test data would do.
6. Check structure and naming against the team convention (one trigger per object, logic in a handler); confirm no scheduled or batch job blocks the deploy of a changed class.
7. Record blocking vs advisory items in `templates/code-review-checklist-salesforce-template.md` and attach it to the PR or release record.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No SOQL, DML, or callouts inside loops over query or trigger row collections; totals stay within per-transaction limits for the expected path.
- [ ] Triggers and synchronous services tolerate 200 records without redundant queries or per-row DML.
- [ ] Sharing model is explicit and justified; user-facing queries enforce FLS/CRUD (`WITH USER_MODE`, or `stripInaccessible` on results as appropriate).
- [ ] No `WITH SECURITY_ENFORCED` in new or rewritten code — removed at API 67.0; on a 67.0+ class it does not compile.
- [ ] Any `apiVersion` bump across 67.0 is called out and re-tested as the production persona.
- [ ] Dynamic SOQL/SOSL uses binding or escaping; no string concatenation of raw end-user input into queries.
- [ ] Tests assert outcomes (not only coverage); include bulk and negative cases where behavior branches; avoid `SeeAllData=true` unless documented and unavoidable.
- [ ] Async entry points (`execute`, `start`, schedulable `execute`) respect queueable/batch limits and do not chain blindly into unbounded recursion.
- [ ] Naming matches the team convention and Apex naming guidance; no `System.debug` left for production paths unless behind diagnostic flags.
- [ ] One trigger per object; trigger body contains no business logic (no SOQL, DML, or service calls inline) — all logic routes through a handler class.

---

## Salesforce-Specific Gotchas

Full list with mitigations in `references/gotchas.md`. The three reviewers miss most often:

1. **Trigger row batch size** — triggers fire on chunks of up to 200 records; always review with a 200-row test.
2. **Trigger sharing context is version-dependent** — a trigger body has no sharing keyword and runs without sharing, but on 67.0+ its unqualified SOQL/DML run in user mode.
3. **`apiVersion` bumps are behaviour changes** — the 67.0 defaults apply per file the moment its metadata version changes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PR / release notes | Checklist results with blocking vs advisory labels |
| Checker output | `check_code_review_checklist_salesforce.py` ERROR/WARN lines attached to the review |
| Linked doc citations | Pointer to Apex limits, testing, or trigger best-practice pages when educating authors |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | Before/after fixes: SOQL in a trigger loop, assertion-free tests, undocumented elevation |
| `references/gotchas.md` | Seven platform behaviours a reviewer must check, each with an avoidance rule |
| `references/llm-anti-patterns.md` | Review conclusions AI assistants get wrong in this domain |
| `references/well-architected.md` | Pillar framing and the official sources behind each claim |
| `references/review-walkthrough.md` | A worked review of one PR from checker run to findings table |

---

## Related Skills

- `security/secure-coding-review-checklist` — Deep AppExchange-style security review (XSS, CSRF, injection focus).
- `devops/continuous-integration-testing` — Wiring tests and test levels in CI pipelines.
- `devops/pre-deployment-checklist` — Manifest and deployment package hygiene before promote.
