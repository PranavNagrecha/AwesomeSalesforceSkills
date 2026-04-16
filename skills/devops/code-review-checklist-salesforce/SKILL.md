---
name: code-review-checklist-salesforce
description: "Structured Salesforce code review for Apex, triggers, async, and tests before merge or deployment — governor limits, bulk-safe triggers, CRUD/FLS and sharing posture, meaningful tests, and naming consistency. NOT for AppExchange security-review-only deep dives (use the security secure-coding checklist), network penetration testing, or org-wide permission model design without code artifacts."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "peer review Apex trigger before production deployment"
  - "Salesforce code review checklist for governor limits and bulkification"
  - "verify our Apex handles two hundred records without SOQL in loops"
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Code Review Checklist Salesforce

This skill activates when a team needs a repeatable, platform-grounded review of Salesforce custom code before merging or promoting a release. It complements CI by giving human reviewers (or an agent) a single pass through the categories that most often cause production regressions or deployment failures: bulk safety and governor consumption, data access enforcement, test quality, and consistency with Salesforce naming and structure guidance.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the execution entry points (trigger on `Account`, `@AuraEnabled` method, REST, batch `execute`, etc.) and the maximum batch size they must support (200 for synchronous trigger contexts).
- Confirm sharing intent: `with sharing`, `without sharing`, `inherited sharing`, or explicit `WITH SECURITY_ENFORCED` / `WITH USER_MODE` patterns — mismatches here are data leaks, not style issues.
- Pull the latest local test run or CI output so coverage numbers are not mistaken for assertion quality.

---

## Core Concepts

### Governor limits and bulk safety

Salesforce enforces per-transaction limits on SOQL, DML, heap, CPU, and callouts. Code that issues queries or DML inside a loop over trigger records scales linearly with batch size and fails at 200. The review goal is constant work per transaction: collect ids, query once, map results, update collections. Async jobs get their own limit scope; still avoid unbounded queries inside loops because heap and CPU compound.

### CRUD, FLS, and sharing

Reading or writing data without respecting the running user’s permissions is both a security defect and a deployment risk. Prefer `WITH USER_MODE` on inline SOQL where appropriate, `WITH SECURITY_ENFORCED` when you need sharing-aware queries that fail closed on FLS violations, and `Security.stripInaccessible` when returning dynamic query rows to callers. Triggers run in system context unless the class uses sharing keywords — call that out explicitly in review.

### Tests as contract, not decoration

Org-wide coverage gates exist, but reviewers should insist on assertions that prove behavior, `@testSetup` for shared data, and negative paths (expected exceptions, bulk scenarios). Tests that only instantiate classes to raise line coverage hide regressions until production.

### Naming and structure

Consistent class and method names reduce onboarding cost and align with the Apex Developer Guide naming guidance. Triggers should be one per object and thin, delegating to handler layers if your team uses that pattern.

---

## Common Patterns

### Bulkified trigger handler

**When to use:** Any `before` or `after` trigger that touches related records.

**How it works:** Loop `Trigger.new` once to collect keys; run one SOQL per object type; build maps; second loop applies updates to collections; single DML per type outside inner queries.

**Why not the alternative:** Querying inside `for (SObject row : Trigger.new)` produces N+1 SOQL and fails under load.

### USER_MODE for user-facing reads

**When to use:** Inline SOQL in services called from Lightning or Experience Cloud where the running user’s FLS must apply.

**How it works:** Append `WITH USER_MODE` to the SOQL; invalid field access throws instead of leaking data.

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

---

## Recommended Workflow

1. Map entry points and data flows from the diff; note trigger context variables used (`Trigger.newMap`, etc.).
2. Walk the governor and bulk section of the checklist: SOQL/DML/callouts per loop, collection sizes, queries against large objects.
3. Verify CRUD/FLS and sharing: keywords on class, SOQL modifiers, and any `as System` or elevated paths.
4. Read test classes: assert messages, bulk test methods (200 rows), and failure expectations; run or inspect CI output.
5. Scan naming (class/trigger/test naming), dead code, and debug statements left in the branch.
6. Record blocking vs advisory items in the PR or release template and link to official limit or testing docs when teaching the author.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No SOQL, DML, or callouts inside loops over query or trigger row collections; totals stay within per-transaction limits for the expected path.
- [ ] Triggers and synchronous services tolerate 200 records without redundant queries or per-row DML.
- [ ] Sharing model is explicit and justified; user-facing queries enforce FLS/CRUD (`WITH USER_MODE`, `WITH SECURITY_ENFORCED`, or `stripInaccessible` on results as appropriate).
- [ ] Dynamic SOQL/SOSL uses binding or escaping; no string concatenation of raw end-user input into queries.
- [ ] Tests assert outcomes (not only coverage); include bulk and negative cases where behavior branches; avoid `SeeAllData=true` unless documented and unavoidable.
- [ ] Async entry points (`execute`, `start`, schedulable `execute`) respect queueable/batch limits and do not chain blindly into unbounded recursion.
- [ ] Naming matches team conventions and Apex naming guidance; no `System.debug` left for production paths unless behind diagnostic flags.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Trigger row batch size** — Triggers fire with up to 200 records; code that worked in a five-record developer test fails in full batches. Always review with 200-row tests.
2. **System context in triggers** — Apex triggers do not use the running user’s sharing by default for the trigger’s own class unless you use sharing keywords or user-mode SOQL. Data exposure reviews must include this.
3. **Governor scope in test vs production** — Starting/stopping tests and async testing can mask limit issues; validate hot paths in synchronous integration-style tests where limits match production transaction scope.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PR / release notes | Checklist results with blocking vs advisory labels |
| Linked doc citations | Pointer to Apex limits, testing, or trigger best-practice pages when educating authors |

---

## Related Skills

- `security/secure-coding-review-checklist` — Deep AppExchange-style security review (XSS, CSRF, injection focus).
- `devops/continuous-integration-testing` — Wiring tests and test levels in CI pipelines.
- `devops/pre-deployment-checklist` — Manifest and deployment package hygiene before promote.
