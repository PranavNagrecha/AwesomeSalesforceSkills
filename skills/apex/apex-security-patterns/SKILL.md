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
  - "verify inner class and subclass sharing inheritance"
  - "check default sharing mode after API 67 version bump"
inputs:
  - "entry point such as AuraEnabled, REST, Flow-invocable, trigger handler, or Batch"
  - "required data access model for records, objects, and fields"
  - "whether the code is read-heavy, write-heavy, or both"
outputs:
  - "security design recommendation for execution context and access enforcement"
  - "review findings for sharing, CRUD/FLS, and system-context risks"
  - "secure service-layer pattern for reads and writes"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-07
---

Use this skill when Apex security needs to be explicit rather than assumed. The purpose is to choose the right sharing model, enforce CRUD and FLS deliberately on reads and writes, and prevent user-facing entry points from silently operating in broader system context than intended.

## Before Starting

- What is the actual entry point: `@AuraEnabled`, REST resource, invocable action, trigger helper, Queueable, or Batch?
- Should the code honor the caller’s record visibility, or is there a documented reason it must run with elevated access?
- Does the code only read data, mutate data, or dynamically choose fields or objects?

## Core Concepts

### Sharing Keywords Set The Record-Access Boundary

`with sharing`, `without sharing`, and `inherited sharing` are design choices, not style preferences. `with sharing` enforces row-level sharing rules for the class. `without sharing` explicitly widens record visibility and must be justified — for record-visibility purposes it lets the code see records as if the running user had Modify All Data. `inherited sharing` makes the class adopt the caller’s sharing model and is often the safest default for reusable service layers that should not surprise reviewers.

Do not lean on the default. In API version 67.0 and later, a class with no explicit sharing declaration runs in `with sharing` mode. That is a safer default than older versions, but it also means a class that genuinely needs elevated visibility can silently start enforcing sharing after an API-version bump, and older code being uplifted may change behavior. Declare the intended mode explicitly rather than depending on the version default.

### Sharing Mode Resolves By Definition, Not By Call Site

Two inheritance and call-chain rules trip up reviewers who assume sharing "flows down" like a normal variable:

- **A method's enforcement is fixed by where it is defined, not by who calls it.** A method defined in a `with sharing` class still enforces sharing rules even when called from a `without sharing` class, and vice versa. You cannot widen or narrow a method's sharing by changing the caller.
- **Class inheritance and inner classes behave differently.** A class *without* its own declaration that `extends` a parent adopts the parent's sharing mode across the chain. But inner classes do **not** adopt the outer (container) class's mode — each inner class needs its own declaration or it falls back to the version default.
- **`inherited sharing` resolves at the entry point.** When an `inherited sharing` class is itself the top-level entry point — an Aura component controller, an `@AuraEnabled` method called from LWC, a Visualforce controller, an Apex REST service, or an asynchronous Apex class — it runs in `with sharing`. It runs `without sharing` only when explicitly called from an already-established `without sharing` context. This is what makes `inherited sharing` the least-surprising default for reusable services.

### Triggers Are Always `without sharing` But DML Defaults To User Mode

Apex triggers cannot carry an explicit sharing keyword and always run implicitly in a `without sharing` context. That does not mean trigger DML ignores field and object permissions: database operations run in user mode unless system mode is explicitly specified, and user mode overrides the trigger's `without sharing` context for the operation. Review trigger logic on the record-visibility axis (it sees everything) separately from the CRUD/FLS axis (user-mode DML still applies).

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

- [ ] Every public or global Apex class declares `with`, `without`, or `inherited sharing` intentionally rather than relying on the API 67.0+ `with sharing` default.
- [ ] Inner classes and `extends`-only subclasses have their intended sharing verified — inner classes do not inherit the outer class's mode, and undeclared subclasses adopt the parent's mode.
- [ ] Cross-call sharing is judged by where each method is defined, not by the sharing mode of the caller.
- [ ] Triggers are reviewed as implicitly `without sharing` for visibility, with DML still checked for the correct user-mode/system-mode intent.
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
5. **Relying on the sharing default is fragile** — in API 67.0+ an undeclared class runs `with sharing`, so uplifting older code or bumping the API version can silently flip enforcement; declare the mode explicitly.
6. **Inner classes do not inherit the outer class's sharing** — a `with sharing` outer class does not make its inner classes safe; each inner class needs its own declaration.
7. **A trigger's `without sharing` context does not disable FLS** — trigger DML still runs in user mode unless system mode is explicitly requested.

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
