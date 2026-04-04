---
name: omnistudio-security
description: "Use when designing or reviewing OmniStudio security across OmniScripts, Integration Procedures, DataRaptors, custom LWCs, Apex actions, guest-user exposure, and outbound HTTP actions. Triggers: 'OmniStudio security', 'guest user omniscript', 'DataRaptor CRUD FLS', 'OmniStudio Apex security', 'HTTP action data exposure'. NOT for general portal identity architecture or generic Apex security reviews when OmniStudio is not the main surface."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I secure OmniStudio for external users"
  - "DataRaptor CRUD and FLS review"
  - "guest user omniscript security concern"
  - "OmniStudio HTTP action exposing too much data"
  - "custom Apex action behind OmniStudio review"
tags:
  - omnistudio-security
  - guest-users
  - dataraptor-security
  - http-action
  - secure-apex
inputs:
  - "whether the OmniStudio surface is internal, portal, or guest-facing"
  - "which DataRaptors, IPs, LWCs, and Apex actions are involved"
  - "what data is read, written, or sent to external systems"
outputs:
  - "OmniStudio security review findings"
  - "guest and external-user hardening guidance"
  - "data exposure and secure-boundary recommendations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# OmniStudio Security

Use this skill when OmniStudio must be reviewed as a real application boundary, not just as a convenience layer. OmniScripts, DataRaptors, Integration Procedures, and custom Apex or LWC extensions can all expose or mutate data. Security defects usually appear where teams assume the OmniStudio layer is safe by default and skip the same rigor they would apply to a public API or site-exposed application.

The key is to review the whole chain: who the user is, what data the asset can access, which server-side code runs, what gets returned to the client, and what gets sent outside Salesforce. Guest and portal scenarios need the tightest design because broad Apex, permissive DataRaptor contracts, or overexposed HTTP responses become visible faster there than in internal-only use.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the OmniStudio surface internal, authenticated external, or guest-facing?
- Which OmniStudio assets are in play: OmniScript, Integration Procedure, DataRaptor, FlexCard, or custom component?
- Does the chain call Apex, invoke HTTP actions, or write data through DataRaptor Load?
- What is the minimum data the caller truly needs to see or modify?

---

## Core Concepts

### OmniStudio Does Not Replace Platform Security

CRUD, FLS, sharing, Apex execution context, and least-privilege integration design still matter. OmniStudio configuration does not automatically secure a weak server boundary.

### External Context Changes The Threat Model

Internal service processes and public or portal flows are not equivalent. Guest and portal users need a narrower data contract, tighter Apex review, and stronger exposure controls.

### Outbound And Inbound Data Contracts Need Review

DataRaptor outputs, Integration Procedure responses, and HTTP action payloads should return only what the consumer needs. Avoid treating intermediate data as safe to send simply because OmniStudio generated it.

### Custom Apex And LWC Are Security Multipliers

The riskiest OmniStudio assets are often the ones that bridge into Apex or custom client components. Their sharing model, CRUD/FLS enforcement, and external exposure are part of the OmniStudio review.

---

## Common Patterns

### Least-Data Response Pattern

**When to use:** OmniStudio returns data to OmniScript, FlexCard, or an external-facing surface.

**How it works:** Shape responses narrowly, strip internal-only fields, and separate operator diagnostics from end-user payloads.

**Why not the alternative:** Over-returned data becomes accidental exposure.

### Secure Extension Boundary Pattern

**When to use:** OmniStudio depends on Apex or custom LWC behavior.

**How it works:** Use explicit sharing and CRUD/FLS enforcement in Apex, and treat the component or action as a secure service boundary instead of a convenience helper.

### External-User Narrowing Pattern

**When to use:** The same business process has both internal and portal or guest variants.

**How it works:** Narrow fields, actions, and server dependencies for the external path instead of reusing the internal design unchanged.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Guest or portal OmniScript collects public input | Minimal field and action surface | Reduces exposure risk |
| Integration Procedure calls an external system | Named Credentials and narrow response contract | Safer auth and data handling |
| Custom Apex action sits behind OmniStudio | Explicit sharing and CRUD/FLS review | OmniStudio does not secure Apex automatically |
| DataRaptor writes records | Review write contract like any other data API | Declarative write paths still mutate data |
| Internal and external variants differ | Split or narrow the external contract | Safer than one broad reusable path |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] User context is explicit: internal, portal, or guest.
- [ ] Apex extensions declare and enforce security intentionally.
- [ ] DataRaptor and IP outputs return only necessary fields.
- [ ] HTTP actions use secure endpoint and credential patterns.
- [ ] External-user variants are narrowed rather than copied from internal designs.
- [ ] Sensitive diagnostics are not leaked through business-facing responses.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Declarative assets can still expose broad data** - DataRaptor and IP responses are still application contracts.
2. **Guest and portal access magnify small server mistakes** - weak Apex behind OmniStudio becomes a production security issue quickly.
3. **HTTP action security is not only about authentication** - response shape and downstream logging still matter.
4. **A secure internal OmniStudio design may be unsafe externally** - user context changes what "safe enough" means.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OmniStudio security review | Findings on user context, data exposure, and extension safety |
| External-user hardening plan | Guidance for guest and portal narrowing |
| Secure-boundary recommendation | How to treat Apex, DataRaptors, and HTTP actions safely |

---

## Related Skills

- `omnistudio/integration-procedures` - use when HTTP action and orchestration safety is the main technical surface.
- `apex/apex-security-patterns` - use when the real issue sits in Apex execution context and CRUD/FLS enforcement.
- `flow/flow-for-experience-cloud` - use when the external-facing experience is primarily Flow rather than OmniStudio.
