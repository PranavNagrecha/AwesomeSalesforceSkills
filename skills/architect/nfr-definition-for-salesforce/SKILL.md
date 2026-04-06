---
name: nfr-definition-for-salesforce
description: "Defining measurable non-functional requirements for Salesforce implementations: performance SLIs, scalability targets, availability SLAs, security and compliance requirements, usability benchmarks. Use when starting architecture design or preparing for go-live sign-off. NOT for technical implementation of those requirements. NOT for HA/DR planning (use ha-dr-architecture). NOT for individual governor limit investigation (use limits-and-scalability-planning). NOT for security controls implementation (use security-architecture-review)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Performance
triggers:
  - "how do we define non-functional requirements for our Salesforce project"
  - "what performance targets should we set before go-live"
  - "how do we document availability and compliance requirements for Salesforce"
  - "what SLAs should we agree with the business before launching on Salesforce"
  - "how do we capture scalability requirements so the architect can design appropriately"
tags:
  - nfr
  - performance
  - scalability
  - availability
  - compliance
  - well-architected
  - sli
  - sla
  - usability
inputs:
  - "Project scope and business domain (e.g. Sales Cloud, Service Cloud, Experience Cloud)"
  - "Regulatory context (GDPR, HIPAA, PCI-DSS, government cloud)"
  - "Expected user count and data volumes at launch and at 3-year horizon"
  - "Integration landscape — external systems, data flows, expected transaction volumes"
  - "Business criticality — what happens when Salesforce is unavailable for 1 hour vs 1 day"
outputs:
  - "NFR register document covering all five categories with measurable acceptance criteria"
  - "Governor limit translation table — business scale targets mapped to Salesforce platform ceilings"
  - "Shared responsibility matrix for availability (Salesforce infrastructure vs. customer data)"
  - "Compliance control checklist tied to applicable regulations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# NFR Definition for Salesforce

This skill activates when a team needs to define and document non-functional requirements (NFRs) for a Salesforce implementation before design begins or before go-live sign-off. It produces a structured NFR register with measurable acceptance criteria grounded in Salesforce platform realities: governor limits, the shared responsibility availability model, compliance control requirements, and usability benchmarks.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Salesforce org edition and feature set — NFRs for a Government Cloud org with Shield differ substantially from a standard Enterprise edition org.
- Establish the business criticality tier: what is the cost of one hour of downtime, one day of data unavailability, or a compliance breach? This sets the stakes for each NFR category.
- Identify the 3-year scale horizon — user count, record counts per major object, daily transaction volume, API call volume. Governor limits are hard ceilings; you need headroom calculations now, not at go-live.
- Confirm which regulations apply. GDPR, HIPAA, and PCI-DSS each impose specific technical controls that must appear as NFRs, not as vague security goals.
- The most common wrong assumption: "Salesforce handles availability — we don't need to define it." This confuses infrastructure uptime (Salesforce's responsibility) with data recovery, custom code reliability, and integration availability (customer's responsibility).

---

## Core Concepts

### NFR Categories for Salesforce

The five categories that must always appear in a Salesforce NFR register, mapped to Well-Architected pillars:

1. **Performance** (Performance Efficiency pillar) — Page load times, report execution times, batch job completion windows, API response times. Must be expressed as Service Level Indicators (SLIs): "95th-percentile Lightning page load under 3 seconds measured in a Full sandbox." Vague targets ("fast") cannot be tested.

2. **Scalability** (Performance Efficiency + Reliability pillars) — Salesforce governor limits are hard, non-negotiable platform ceilings, not soft guidelines. Every scalability NFR must be expressed relative to these limits. Key limits: SOQL rows per transaction (50,000), DML statements per transaction (150), CPU time per transaction (10,000 ms Apex), heap size (6 MB sync / 12 MB async), synchronous callout timeout (120 s), daily API request allocation (varies by edition/user count). Architect for 50% headroom against any limit that correlates with data growth.

3. **Availability** (Reliability pillar) — Salesforce Trust publishes a 99.9% infrastructure uptime SLA. This covers the platform — it does NOT cover: custom Apex code reliability, integration availability, org-to-org data sync, or data recovery time after a misconfigured bulk delete. The NFR register must distinguish infrastructure availability (Salesforce's SLA) from application availability (team's responsibility) and define RPO/RTO for backup scenarios.

4. **Security and Compliance** (Trusted pillar) — Regulations impose specific technical controls. GDPR requires data maps, right-to-erasure workflows, and audit logs. HIPAA requires encryption at rest (Shield Platform Encryption or Field Encryption), audit trails (Field History Tracking or Event Monitoring), and BAA with Salesforce. PCI-DSS scopes may require tokenisation or out-of-scope data routing. Each applicable regulation should generate a named NFR with a testable acceptance criterion.

5. **Usability** (Easy pillar) — Page load time (overlap with performance), field count per page layout (recommend ≤ 30 visible fields per layout for cognitive load), mobile readiness (percentage of workflows completable on Salesforce Mobile), accessibility compliance (WCAG 2.1 AA for public or government-facing pages).

### Well-Architected Framing

Salesforce organises its Well-Architected Framework across three top-level pillars: Trusted (security, compliance, reliability), Easy (usability, process efficiency), and Adaptable (scalability, resilience, composability). Every NFR category maps to at least one pillar. Using this framing ensures NFRs survive architecture reviews and are traceable to platform guidance.

### Measurability Requirement

An NFR is only useful if it can be tested. Every NFR must include:
- A metric (what to measure)
- A threshold (acceptable vs. unacceptable value)
- A measurement method (where, when, and how to measure)
- An environment qualifier (sandbox tier, load profile)

Example of an untestable NFR: "The system must be responsive." Example of a testable NFR: "95% of Lightning record page loads complete in under 3 seconds, measured via browser-side performance tracing in a Full sandbox with 10 concurrent users simulated."

---

## Common Patterns

### Pattern 1: Governor Limit Translation

**When to use:** When business stakeholders provide scale targets like "we expect 500,000 cases per year" or "50 integrations running hourly."

**How it works:**
1. Collect business scale numbers (records/day, concurrent users, API calls/day, batch window).
2. Map each to the relevant governor limit category.
3. Calculate expected utilisation as a percentage of the limit.
4. Flag any dimension that exceeds 50% utilisation at the 3-year horizon as an architectural constraint requiring a design decision (e.g. async processing, chunking, Platform Events).

**Why not the alternative:** Treating governor limits as implementation details discovered during development leads to emergency re-architecture at go-live. They are first-class architectural constraints and must appear in the NFR register.

### Pattern 2: Compliance Control Decomposition

**When to use:** When the project operates under a named regulation (GDPR, HIPAA, PCI-DSS, SOC 2).

**How it works:**
1. Identify each applicable regulation.
2. For each regulation, list the specific technical controls it requires.
3. For each control, create a named NFR with a testable acceptance criterion tied to a Salesforce feature (Shield Encryption, Event Monitoring, Field Audit Trail, Connected App policies).
4. Assign an owner (Salesforce admin, security team, data officer).

**Why not the alternative:** Listing "must be GDPR compliant" as a single NFR is untestable and unassignable. It will be interpreted differently by every reviewer and will fail a compliance audit.

### Pattern 3: Availability Responsibility Mapping

**When to use:** Always — for every implementation. The shared responsibility model is never optional to document.

**How it works:**
1. List every availability concern: infrastructure uptime, custom code reliability, batch job completion, integration uptime, data recovery.
2. For each concern, assign responsibility to either Salesforce (infrastructure SLA) or the customer team.
3. For customer-owned concerns, define RPO (recovery point objective) and RTO (recovery time objective).
4. Document how each concern will be monitored (Salesforce Health Check, custom monitoring flows, integration heartbeats).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Performance target is vague ("fast enough") | Define SLI with percentile, threshold, and measurement method | Untestable NFRs cannot gate go-live or be used in capacity planning |
| Scale target exceeds 50% of a governor limit at 3-year horizon | Raise as architectural constraint requiring design decision now | Governor limits cannot be increased; redesign is cheaper before build |
| Regulation named but controls not enumerated | Decompose into per-control NFRs with Salesforce feature mapping | Audit-ready compliance requires control-level traceability |
| Business says "we need 99.99% uptime" | Separate infrastructure SLA (Salesforce's 99.9%) from application reliability (team's responsibility) | Salesforce's SLA covers infrastructure only; custom code is team-owned |
| Project lacks usability NFRs | Add layout field count limits, mobile completion targets, WCAG level | Usability regressions are caught late and expensive to fix post-launch |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Collect project scope — org edition, feature set, regulatory context, integration landscape, and 3-year user and data volume projections.
2. For each of the five NFR categories (performance, scalability, availability, security/compliance, usability), draft at least two measurable NFRs using the SLI format: metric, threshold, measurement method, environment qualifier.
3. Translate business scale targets into governor limit utilisation percentages. Flag any dimension exceeding 50% at the 3-year horizon as an architectural constraint.
4. Map each applicable regulation to the specific Salesforce features that satisfy its controls. Create one NFR per control, not one NFR per regulation.
5. Document the availability shared responsibility split: which availability concerns are covered by Salesforce's infrastructure SLA, and which are customer-owned (with RPO/RTO defined).
6. Review the NFR register against the Well-Architected pillars — Trusted, Easy, Adaptable — to confirm all three are addressed.
7. Validate each NFR has a test method and an assigned owner. Remove or escalate any NFR that cannot be verified in a test environment.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every NFR has a metric, threshold, measurement method, and environment qualifier
- [ ] All applicable governor limits are represented as scalability NFRs with utilisation calculations
- [ ] The availability NFR register separates Salesforce infrastructure SLA from customer-owned availability
- [ ] Each applicable regulation has been decomposed into per-control NFRs, not a single "must be compliant" statement
- [ ] Usability NFRs include page load time, layout field count limits, and mobile readiness targets
- [ ] Every NFR has an assigned owner
- [ ] No NFR uses vague adjectives (fast, secure, reliable) without a measurable threshold

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Governor limits are per-transaction, not per-request** — SOQL row limits (50,000), DML statements (150), and CPU time (10,000 ms) reset at transaction boundaries. An NFR that says "the system must handle 1 million records per day" is valid at the batch level but a single synchronous transaction cannot process more than 50,000 rows. NFRs must specify the unit of measurement and the processing mode (sync vs. async).

2. **Salesforce's 99.9% uptime SLA does not cover org-level outages from bad deployments** — A Metadata API deployment that breaks a critical trigger is not covered by the Trust infrastructure SLA. Customer-owned application availability must be explicitly scoped in the NFR register with a separate RTO/RPO.

3. **Scale testing requires Full sandbox — Developer Pro is not a valid proxy** — Developer Pro sandboxes have a 200 MB storage limit and do not replicate production data volume or record distribution. Performance NFRs validated only in Developer Pro sandboxes will produce invalid results. Full sandboxes are the minimum for load-representative performance testing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| NFR Register | Structured document with one row per NFR: category, metric, threshold, measurement method, environment, owner, status |
| Governor Limit Translation Table | Business scale targets mapped to Salesforce limit categories with utilisation percentages at launch and 3-year horizon |
| Availability Responsibility Matrix | Per-concern split between Salesforce infrastructure SLA and customer-owned availability, with RPO/RTO for customer-owned items |
| Compliance Control Checklist | Per-regulation breakdown of required controls mapped to Salesforce features, with testable acceptance criteria |

---

## Related Skills

- ha-dr-architecture — use after NFR definition to design the technical solution for availability and recovery NFRs
- limits-and-scalability-planning — use to investigate specific governor limit headroom once scalability NFRs are defined
- security-architecture-review — use to validate that security and compliance NFRs are met by the org configuration
- well-architected-review — use to assess the full implementation against all three Well-Architected pillars
