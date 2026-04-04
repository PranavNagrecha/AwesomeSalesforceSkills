---
name: apex-security-patterns
description: "Use when designing, reviewing, or debugging Apex execution context, sharing keywords, CRUD/FLS enforcement, system-vs-user mode behavior, or secure write patterns. Triggers: 'with sharing', 'inherited sharing', 'stripInaccessible', 'AuraEnabled security', 'CRUD FLS'. NOT for SOQL injection review alone — use apex/soql-security for query-specific hardening."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - apex-security
  - inherited-sharing
  - stripinaccessible
  - crud-fls
  - user-mode
triggers:
  - "with sharing without sharing inherited sharing decision"
  - "how do I enforce CRUD and FLS in Apex updates"
  - "AuraEnabled method running in system context"
  - "stripInaccessible for DML pattern"
  - "secure Apex service layer review"
inputs:
  - "entry point such as AuraEnabled, REST, Flow-invocable, trigger handler, or Batch"
  - "required data access model for records, objects, and fields"
  - "whether the code is read-heavy, write-heavy, or both"
outputs:
  - "security design recommendation for execution context and access enforcement"
  - "review findings for sharing, CRUD/FLS, and system-context risks"
  - "secure service-layer pattern for reads and writes"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when Apex security needs to be explicit rather than assumed. The purpose is to choose the right sharing model, enforce CRUD and FLS deliberately on reads and writes, and prevent user-facing entry points from silently operating in broader system context than intended.

## Before Starting

- What is the actual entry point: `@AuraEnabled`, REST resource, invocable action, trigger helper, Queueable, or Batch?
- Should the code honor the caller’s record visibility, or is there a documented reason it must run with elevated access?
- Does the code only read data, mutate data, or dynamically choose fields or objects?

## Core Concepts

### Sharing Keywords Set The Record-Access Boundary

`with sharing`, `without sharing`, and `inherited sharing` are design choices, not style preferences. `with sharing` enforces row-level sharing rules for the class. `without sharing` explicitly widens record visibility and must be justified. `inherited sharing` makes the class adopt the caller’s sharing model and is often the safest default for reusable service layers that should not surprise reviewers.

### Record Access Is Not CRUD/FLS Enforcement

This is the most common misconception in Apex security. `with sharing` affects row visibility; it does not automatically enforce object permissions or field-level security. Reads and writes still need explicit handling such as `WITH USER_MODE`, `WITH SECURITY_ENFORCED`, `Security.stripInaccessible`, or Schema describe checks depending on whether the design should fail fast or degrade gracefully.

### User-Facing Entry Points Need Explicit Security

Aura-enabled controllers, REST resources, and other externally callable Apex can easily run with broader access than intended if the class declaration and data-access code are vague. Secure Apex guidance emphasizes making sharing intent explicit and enforcing access in the data path, not assuming the platform will infer the right boundary.

### Secure Writes Need As Much Attention As Secure Reads

Teams often secure queries and then perform unsafe DML on fields the user should not edit. `Security.stripInaccessible` is a strong pattern for mutating records safely while preserving a clear list of removed fields for auditing or logging.

## Common Patterns

### `inherited sharing` Service Layer

**When to use:** Reusable services are called from multiple entry points and should respect the caller’s sharing model.

**How it works:** Declare the service `inherited sharing`, keep high-risk elevation isolated to narrow helper classes, and document every justified `without sharing` boundary.

**Why not the alternative:** Omitting a sharing keyword leaves intent ambiguous and makes reviews harder.

### Read With User Context, Write With `stripInaccessible`

**When to use:** Code both queries and updates data on behalf of a user.

**How it works:** Use `WITH USER_MODE` or another explicit read-enforcement strategy for queries, then sanitize outbound records with `Security.stripInaccessible` before DML.

### Allowlist Dynamic Access

**When to use:** The code allows a caller to choose fields, sort orders, or objects dynamically.

**How it works:** Validate object and field names against Schema describe metadata and allowlists before using them.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Reusable service should respect the caller’s sharing boundary | `inherited sharing` | Clear and least surprising behavior |
| User-facing code reads data for the current user | Explicit user-context read pattern such as `WITH USER_MODE` | Sharing alone is not enough |
| User-facing code updates records | `Security.stripInaccessible` before DML | Prevents unauthorized field writes |
| Documented admin or maintenance process truly needs elevated access | Narrow `without sharing` helper with explicit justification | Keeps privilege elevation contained |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Every public or global Apex class declares `with`, `without`, or `inherited sharing` intentionally.
- [ ] Reviews distinguish record access from CRUD/FLS enforcement instead of conflating them.
- [ ] User-facing entry points enforce access in both reads and writes.
- [ ] `without sharing` usage is narrow, justified, and documented.
- [ ] Dynamic field or object access is allowlisted through Schema describe or equivalent validation.
- [ ] Secure write paths inspect or log stripped fields when that matters operationally.

## Salesforce-Specific Gotchas

1. **`with sharing` does not enforce CRUD or FLS** — it only addresses row visibility.
2. **Aura-enabled Apex can still expose too much data if the query or DML path is not explicitly secured** — the class declaration alone is not enough.
3. **`without sharing` in the wrong layer silently widens access for everything below it** — security reviews must trace the call chain, not just the top-level controller.
4. **Secure read patterns and secure write patterns are different** — a class can query safely and still perform unsafe DML if writes are not sanitized.

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex security review | Findings on sharing intent, CRUD/FLS enforcement, and system-context risk |
| Security decision tree | Guidance for `with sharing`, `without sharing`, `inherited sharing`, and data-access enforcement |
| Secure code pattern | Read/write pattern using explicit query enforcement and `stripInaccessible` |

## Related Skills

- `apex/soql-security` — use when the main concern is injection or SOQL-specific field-access patterns.
- `apex/callouts-and-http-integrations` — use when the security risk is remote authentication, endpoint governance, or outbound data transfer.
- `apex/test-class-standards` — use alongside this skill to design tests for sharing-sensitive and FLS-sensitive behavior.
