# Well-Architected Notes — Apex Security Patterns

## Relevant Pillars

### Security

This skill is directly about the Security pillar. It defines who can see records, who can read fields, who can update fields, and when system context is allowed to override those defaults.

Tag findings as Security when:
- a class omits or misuses its sharing declaration
- CRUD/FLS enforcement is missing on reads or writes
- user-facing Apex runs with broader access than intended

### Reliability

Security bugs also become reliability bugs when users see inconsistent behavior or when elevated access causes data changes that violate business expectations.

Tag findings as Reliability when:
- access checks are applied inconsistently across read and write paths
- the same service behaves differently depending on ambiguous sharing intent
- security sanitization removes fields silently without operational visibility where that visibility matters

## Architectural Tradeoffs

- **Inherited sharing vs explicit `with sharing`:** inherited sharing is often best for reusable services, but top-level entry points still need deliberate declarations.
- **Fail-fast vs graceful degradation:** `WITH USER_MODE` and `WITH SECURITY_ENFORCED` can fail fast; `stripInaccessible` can degrade gracefully by removing inaccessible fields.
- **Elevated-access helpers vs broad elevated layers:** narrow privilege escalation is safer than `without sharing` at the controller boundary.

## Anti-Patterns

1. **Top-level `without sharing` as a shortcut** — easy to write, hard to defend in review.
2. **Query secured, write unsecured** — the most common partial-security design flaw.
3. **Implicit sharing intent** — missing declarations force reviewers to infer behavior instead of verifying it.

## Official Sources Used

- Apex Developer Guide — security and sharing keyword guidance
- Secure Apex Classes — explicit CRUD/FLS and user-context recommendations
- Salesforce Well-Architected Overview — security and reliability framing
