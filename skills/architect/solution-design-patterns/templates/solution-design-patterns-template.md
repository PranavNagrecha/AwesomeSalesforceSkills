# Solution Design Recommendation — Work Template

Use this template when selecting the right automation layer for a Salesforce requirement, reviewing an existing design, or presenting a design recommendation for stakeholder approval.

---

## Scope

**Skill:** `solution-design-patterns`

**Feature or requirement being designed:**
(One sentence describing what the automation must accomplish)

**Date:** (YYYY-MM-DD)

**Author:**

---

## Requirement Classification

### Trigger Type

Select the event that initiates the automation:

- [ ] User initiates an action (button click, form submission)
- [ ] Record is created
- [ ] Record is updated
- [ ] Record is created or updated
- [ ] Scheduled time or interval
- [ ] Platform Event received
- [ ] External system HTTP request (inbound)

### Key Constraints

| Constraint | Answer |
|---|---|
| Requires same-transaction HTTP callout? | [ ] Yes [ ] No |
| Expected record volume per run | (e.g., 1–10 / 100–500 / 1,000+) |
| Logic complexity | [ ] Simple (field default, notification) [ ] Moderate (conditional routing) [ ] Complex (multi-object, branching, data transformation) |
| External system dependency? | [ ] Yes — (name system) [ ] No |
| Who will maintain this long-term? | [ ] Admin [ ] Developer [ ] Both |

---

## Escalation Decision

Work through this checklist in order. **Stop at the first "Yes" answer** — that determines the minimum required layer.

| Question | Answer | Layer implied |
|---|---|---|
| Can the logic be expressed entirely in Flow formulas and standard actions? | [ ] Yes [ ] No | Flow |
| Does the logic require a same-transaction HTTP callout? | [ ] Yes [ ] No | Apex |
| Does bulk processing require explicit governor limit control (200+ records per transaction)? | [ ] Yes [ ] No | Apex |
| Does the use case require a custom UI that standard Lightning components cannot provide? | [ ] Yes [ ] No | LWC |
| Can the custom UI use Lightning Data Service for reads and standard actions for writes? | [ ] Yes [ ] No | LWC without Apex |

### Recommended Layer

**Primary layer:** [ ] Screen Flow [ ] Record-Triggered Flow [ ] Scheduled Flow [ ] Apex Trigger [ ] Apex Queueable / Future [ ] LWC [ ] LWC + Apex

**Reasoning:**
(State which escalation criterion drove the decision, or confirm that no criterion was met and Flow is the correct starting point)

---

## Design Sketch

### Automation Owner per Trigger Event

| Object | Trigger Event | Automation Owner | Purpose |
|---|---|---|---|
| (Object API Name) | (before insert / after update / etc.) | (Flow / Apex trigger / etc.) | (what it does) |

**Confirm:** Is there only one automation owner per trigger event per object? [ ] Yes [ ] No — (document conflict and resolution)

### Configuration Storage

| Config value | Storage mechanism | Reason |
|---|---|---|
| (routing threshold, feature flag, etc.) | [ ] Custom Metadata Type [ ] Custom Label [ ] Hard-coded (flag for remediation) | |

**Hard-coded IDs present?** [ ] None found [ ] Found — must be moved to CMDT before deployment

### Layer Decoupling (if callout required)

If the design requires both declarative logic and a same-transaction callout:

- [ ] Platform Event fired by Flow → Apex Platform Event trigger handles callout
- [ ] Apex `@future(callout=true)` for post-transaction callout
- [ ] Apex Queueable with callout support (preferred over `@future` for chaining and monitoring)

---

## Legacy Automation Audit

Check for existing automation on each object involved in this design:

| Object | Process Builders active? | Workflow Rules active? | Existing Flows? | Existing Apex Triggers? |
|---|---|---|---|---|
| | [ ] Yes [ ] No | [ ] Yes [ ] No | [ ] Yes, count: | [ ] Yes, count: |

**Action required for each legacy item:**
- Process Builder: [ ] Deactivate before go-live [ ] Migrate to Flow (included in this work) [ ] Defer — document dependency
- Workflow Rule: [ ] Already inactive [ ] Migrate to Flow (included in this work) [ ] Defer — document dependency

---

## Future-Proofing Checklist

- [ ] No Salesforce record IDs hard-coded in Flow conditions, Apex, or CMDT field defaults
- [ ] Configuration values (thresholds, routing rules, feature flags) stored in Custom Metadata Types
- [ ] No new Process Builder automations created in this work
- [ ] No new Workflow Rules created in this work
- [ ] One designated automation owner per trigger event per object
- [ ] Apex triggers delegate to handler classes (no DML or SOQL directly in the trigger file)
- [ ] Flow loops do not contain Get Records elements (SOQL queries outside loops only)
- [ ] LWC chosen only where a documented standard component gap exists

---

## Governor Limit Budget Estimate

Estimate the limits consumed in a single transaction for the designed automation:

| Resource | Budget (per transaction) | Estimated usage | Notes |
|---|---|---|---|
| SOQL queries | 100 | | (count Flow Get Records + Apex queries combined) |
| DML statements | 150 | | (count Flow Update/Create + Apex DML combined) |
| Flow interview elements | 2,000 | | (estimate loop iterations × elements per iteration) |
| CPU time (ms) | 10,000 | | (Apex-heavy designs; less relevant for Flow-only) |

**Risk flag:** If any resource exceeds 50% of budget in a low-volume scenario, flag for load testing before production deployment.

---

## Sign-Off

| Role | Name | Decision |
|---|---|---|
| Architect / Tech Lead | | [ ] Approved [ ] Revise |
| Admin / Flow Owner (if applicable) | | [ ] Approved [ ] No involvement |
| Developer (if Apex involved) | | [ ] Approved [ ] Revise |

**Approved design summary:**
(One paragraph capturing the final decision: which layer, why, key constraints addressed, and any deferred items)
