---
name: stakeholder-raci-for-sf-projects
description: "Use this skill when building, reviewing, or refreshing a RACI (Responsible / Accountable / Consulted / Informed) matrix for a Salesforce project so that every Salesforce-specific decision — data model change, automation tier choice, security model, integration boundary, deployment, license/edition — has exactly one accountable owner and a documented escalation path that downstream agents can route to. Trigger keywords: RACI matrix salesforce project, stakeholder authority salesforce, escalation path salesforce decisions, who approves data model change, salesforce decision rights, REFUSAL_NEEDS_HUMAN_REVIEW routing. NOT for the change advisory board operating model itself (use admin/change-management-and-deployment). NOT for end-user training rollout plans (use admin/change-management-and-training). NOT for the technical mechanics of permission set assignment authority (use admin/permission-set-architecture). NOT for pure stakeholder requirements elicitation (use admin/requirements-gathering-for-sf)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "how do I build a RACI matrix for a Salesforce project"
  - "who is accountable for approving a Salesforce data model change"
  - "what is the escalation path when a Salesforce admin gets blocked"
  - "RACI matrix salesforce stakeholder authority decisions"
  - "stakeholder authority salesforce integration data steward"
  - "escalation path salesforce decisions exec sponsor"
  - "how to map agent refusal codes to human stakeholders for review"
tags:
  - raci
  - stakeholder-management
  - governance
  - escalation
  - decision-rights
  - business-analysis
inputs:
  - "Project phase (discovery, build, UAT, hypercare) and target go-live date"
  - "Org topology — single org, multi-org, M&A, regulated industry context"
  - "Roster of named individuals or roles filling: business sponsor, process owner, data steward, security architect, integration architect, CRM admin lead, release manager, compliance officer, AppExchange owner, end-user representative"
  - "List of Salesforce decision categories in scope (data model, automation, security, integration, deployment, licensing)"
  - "Existing change advisory board (CAB) cadence and quorum rules, if any"
outputs:
  - "Filled RACI matrix as markdown table and machine-readable JSON (one row per decision category, one column per stakeholder role)"
  - "Per-row escalation rule with time-box and trigger condition (when does this go up, to whom, within how long)"
  - "Refusal-code-to-stakeholder map that downstream runtime agents can consult when they emit REFUSAL_NEEDS_HUMAN_REVIEW"
  - "Sponsor / steerco review log showing the matrix has been reviewed and version-locked for the current phase"
  - "Identified gaps — decision categories with no A, A roles overloaded across rows, decisions still owned by the consulting partner instead of the customer"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Stakeholder RACI for Salesforce Projects

This skill activates when a Business Analyst, project manager, or admin lead needs a deterministic method for assigning decision authority on a Salesforce project — and a routing table that the repository's runtime agents can use when they emit `REFUSAL_NEEDS_HUMAN_REVIEW`. The output is a RACI matrix tailored to the Salesforce decision surface (data model, automation tier, security, integration, deployment, licensing) with explicit escalation rules per accountable cell.

---

## Before Starting

Gather this context before drafting the matrix:

- **Phase and version-lock cadence.** A RACI for discovery is not the RACI for build, and neither is the RACI for hypercare. The matrix must be version-locked per phase or it becomes stale within weeks. Confirm the phase you are modelling and the next planned re-review date.
- **Named individuals vs. roles.** Salesforce projects fail when "the architect" or "the admin" is a placeholder — a single physical person must carry the A. Confirm whether the project is staffed enough that every stakeholder role on the canonical list maps to a named person; if not, surface the gap rather than papering over it.
- **Customer vs. partner ownership boundary.** On consulting-led implementations, the most damaging RACI mistake is leaving A-cells with the systems integrator after go-live. Establish up front which A-cells transfer to the customer at hypercare and document the transfer date.
- **Regulatory overlay.** HIPAA, FINRA, PCI, GDPR, SOX each impose a non-negotiable A on a compliance officer for specific decisions (PHI access, trade record retention, cardholder data, data subject rights, financial reporting controls). The compliance officer's A is not negotiable, even if a sponsor wants to push it elsewhere.
- **Existing CAB.** If the org has a change advisory board, the CAB is typically C (consulted) on deployment decisions and may hold A on production deploys for high-blast-radius changes. Capture its cadence and quorum rules — RACI escalations that miss CAB cadence stall.

---

## Core Concepts

### The Salesforce Decision Surface

A generic project RACI lists deliverables. A Salesforce RACI lists *decisions* — because a Salesforce build is a stack of irreversible-or-expensive-to-reverse decisions, not a stack of artifacts. The canonical decision categories every Salesforce RACI must cover:

1. **Data model change** — adding/changing/deleting standard or custom objects, fields, relationships, record types, or external IDs. A decision here ripples through reports, integrations, and security.
2. **Automation tier** — picking Flow vs. Apex vs. Agentforce vs. Approvals vs. Platform Events for a given requirement (see `standards/decision-trees/automation-selection.md`).
3. **Security model** — OWD, role hierarchy, sharing rules, profiles, permission sets, permission set groups, restriction rules, and field-level security (see `standards/decision-trees/sharing-selection.md`).
4. **Integration boundary** — REST vs. Bulk vs. Platform Events vs. CDC vs. Pub/Sub vs. Salesforce Connect vs. MuleSoft (see `standards/decision-trees/integration-pattern-selection.md`), plus the contract with the source/target system.
5. **Deployment** — what gets promoted, when, with what backout plan, and through which sandboxes (see `admin/sandbox-strategy`).
6. **License + edition** — which user license, which add-on (Service Cloud, Sales Cloud, Agentforce, CPQ, OmniStudio, Experience Cloud), edition tier, and feature license assignment.

Every row in the matrix is one of these categories — or a sub-row scoped to a specific object, integration, or release. Resist adding deliverable rows ("build the Account page layout") — those belong in a work-breakdown structure, not a RACI.

### The Canonical Salesforce Stakeholder Roster

The matrix columns come from a fixed roster:

| Role | Typical title | Owns A on | Owns C on |
|---|---|---|---|
| Business sponsor | VP Sales / VP Service / CFO / CIO | Scope, budget, go/no-go gate | Almost everything else |
| Process owner | Director of the affected business function | Business process changes, UAT sign-off | Data model changes that affect their process |
| Data steward | MDM lead / data governance lead | Data model changes, picklist values, dedupe rules, retention | Reports, integrations |
| Security architect | InfoSec / IAM lead | Security model, profile/PSG architecture, sharing | Integrations, data model with PII |
| Integration architect | Enterprise architect / iPaaS lead | Integration boundary + contract | Data model, security |
| CRM admin lead | Salesforce admin / lead BA | Day-to-day config, declarative automation | All technical decisions |
| Release manager | DevOps / release engineer | Deployment, sandbox strategy, environment hygiene | Automation tier when it affects packaging |
| AppExchange owner | The internal sponsor of any installed managed package | Decisions touching the package's namespace | Data model, security |
| Compliance officer | Privacy / risk / compliance lead | Regulatory controls, audit trail, retention | Data model, security, integrations |
| End-user representative | Power user from the affected team | UAT, adoption, training feedback | Process changes |

Keep architects split across **Security architect** and **Integration architect** — collapsing them into a single "Architecture" role is one of the most common RACI mistakes on Salesforce projects.

### R / A / C / I — and the One-A Rule

- **R (Responsible)** — does the work. There can be many Rs per row.
- **A (Accountable)** — owns the outcome and is the single decision-maker. **Exactly one A per row.** This is the load-bearing rule of any RACI; multiple As mean nobody is accountable.
- **C (Consulted)** — two-way conversation before the decision is made. Their input is required, not optional.
- **I (Informed)** — one-way notification after the decision is made.

Additional rules specific to Salesforce projects:

- No A on a Consulted role. If someone is C, they cannot also be A — that contradicts the one-A rule.
- Every row must have at least one R. A row with only A/C/I means the work is unowned.
- An advisory body (CAB, steerco, design authority) is C, never A. They review; the named accountable person decides.
- The data steward is C at minimum on every data model row, even when a process owner holds A.

### Escalation Rules: The "When Does This Go Up?" Question

A RACI without escalation rules is a wall poster. For every A-cell, document:

- **Trigger** — what condition forces escalation (e.g., A and C disagree, time-box exceeded, blast radius exceeds threshold).
- **Target** — who the next-level decision-maker is (typically the sponsor or steerco).
- **Time-box** — how long the A has to decide before escalation auto-fires (e.g., "data model change pending >5 business days escalates to sponsor").

Escalation rules without a time-box silently rot — the project blocks but no alarm trips.

### Mapping RACI to Agent Refusal Codes

The repository's runtime agents emit refusal codes from `agents/_shared/REFUSAL_CODES.md` when they hit a condition that explicitly requires human judgment. The RACI is the routing table that converts a refusal code into a named person.

Canonical mapping:

| Refusal code | Decision category in RACI | Who the BA pings (the A) |
|---|---|---|
| `REFUSAL_NEEDS_HUMAN_REVIEW` | The category named in the refusal `message` | The A on the matching row |
| `REFUSAL_INPUT_AMBIGUOUS` | Whichever category the input concerns | The A on that row |
| `REFUSAL_SECURITY_GUARD` | Security model | Security architect |
| `REFUSAL_POLICY_MISMATCH` | Whichever decision category the policy spans | The A on that row + sponsor (informed) |
| `REFUSAL_MANAGED_PACKAGE` | License + edition (managed package scope) | AppExchange owner |
| `REFUSAL_COMPETING_ARTIFACT` | Data model or automation tier (depends on artifact) | The A on the matching row |
| `REFUSAL_DATA_QUALITY_UNSAFE` | Data model | Data steward |
| `REFUSAL_FEATURE_DISABLED` | License + edition | Business sponsor (cost) + CRM admin lead (enablement) |

Every BA / admin runtime agent's escalation step should look up the refusal code, find the row, and ping the A — with the C on the same row in the loop.

---

## Common Patterns

### Pattern: Greenfield Sales Cloud RACI

**When to use:** First Salesforce implementation, single-org, no managed packages, single-region.

**How it works:** Sponsor (CRO) holds A on scope and license. Process owner (VP Sales Ops) holds A on data model and automation tier. Security architect holds A on security. Integration architect holds A on the one or two inbound feeds. CRM admin lead holds A on day-to-day config. Compliance officer is C on data model and security; not on the critical path.

**Why not the alternative:** Rolling A on the data model into the sponsor in a greenfield is tempting but wrong — sponsors do not have time to decide on every field, and the data steward / process owner is closer to the data semantics.

### Pattern: Regulated Industry RACI (HIPAA / FINRA / PCI)

**When to use:** Health Cloud, Financial Services Cloud, payment-card-handling, or any project where audit findings could be material.

**How it works:** Compliance officer holds A on retention, audit trail, and any decision touching regulated data. Security architect holds A on FLS and sharing for regulated objects. Data steward is C on every row touching regulated data and may hold A on data classification. Sponsor's A on scope must include explicit acceptance that the compliance officer can veto a feature.

**Why not the alternative:** Treating compliance as C on regulated data lets the project ship with a control gap — and the audit catches it six months later. Compliance gets A on the controls; the process owner still owns the business outcome.

### Pattern: M&A Multi-Org RACI

**When to use:** Two or more existing Salesforce orgs being merged or federated post-acquisition.

**How it works:** Two business sponsors (one per legacy org) reporting to a combined steerco; the steerco holds A on org-strategy decisions (merge vs. federate vs. coexist). Each org keeps its own CRM admin lead and process owner with split A on day-to-day decisions. Integration architect holds A on the cross-org integration pattern. A new "data steward (master)" role emerges to hold A on the master data model post-merger.

**Why not the alternative:** Naming a single sponsor too early in an M&A causes one side's stakeholders to disengage. The split-A pattern is uncomfortable but mirrors the actual organizational state until the merger is complete.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Sponsor wants A on every row | Push back; sponsor holds A on scope/budget/go-no-go only | Sponsors cannot decide field-by-field; A loses meaning if everywhere |
| No data steward exists in the org | Surface as a project risk, not a config; ask sponsor to name one | Data model decisions without a steward become technical debt within months |
| Architecture is a single role | Split into security architect and integration architect | Salesforce architecture decisions span domains; one head cannot hold A on both |
| Implementation partner is A on production deploy | Transfer A to internal release manager before hypercare ends | Partners leave; A must live with the customer permanently |
| AppExchange package is in scope | Add AppExchange owner as a column; A on namespace-touching decisions | Managed-package namespace constraints are not negotiable |
| Compliance is C on every regulated row | Promote compliance to A on the regulatory control rows | C is not enough for audit-grade decisions |
| Escalation rule has no time-box | Add one (typically 3–5 business days) | Escalations without a clock silently stall projects |
| Agent emits `REFUSAL_NEEDS_HUMAN_REVIEW` | Look up the decision category in the refusal map; ping the A | This is the runtime use of the matrix |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or BA activating this skill:

1. **Identify stakeholders + roles.** Confirm a named individual exists for every role on the canonical roster. Flag empty roles as project risks before drafting the matrix.
2. **List Salesforce-specific decision categories.** Start with the six canonical categories (data model, automation, security, integration, deployment, license/edition). Add sub-rows only if a category needs scoping (e.g., "data model — Account / Contact / Opportunity" vs. "data model — custom regulatory objects").
3. **Assign R / A / C / I per cell.** Apply the one-A rule, the no-A-on-C rule, and the every-row-has-an-R rule. Run `scripts/check_raci.py` against the JSON to enforce them.
4. **Define the escalation rule per A cell.** For each A, write trigger + target + time-box. No A may ship without an escalation rule.
5. **Map RACI to agent refusal codes.** Fill the refusal-code-to-stakeholder map at the bottom of the matrix using `agents/_shared/REFUSAL_CODES.md`. Every code that ends in `_HUMAN_REVIEW`, `_AMBIGUOUS`, `_GUARD`, `_MISMATCH`, or `_NEEDS_HUMAN_REVIEW` must resolve to a named A.
6. **Review with sponsor and steerco.** A RACI without a sponsor signature is advisory. Capture the review date and the next planned re-review date.
7. **Version-lock per phase.** Tag the matrix with the phase (discovery / build / UAT / hypercare) and the version. The next phase requires a re-review and a new version, not an in-place edit.

---

## Review Checklist

Run through these before publishing the matrix:

- [ ] Every row has exactly one A
- [ ] No row has A on a C role
- [ ] Every row has at least one R
- [ ] Every R/A/C/I value is from the enum (R, A, C, I) — no blanks, no commentary
- [ ] Every A cell has a written escalation rule with trigger + target + time-box
- [ ] Every refusal code in `agents/_shared/REFUSAL_CODES.md` that requires human review resolves to a named A
- [ ] No A is held by the implementation partner past the planned hypercare exit date
- [ ] Compliance officer holds A (not just C) on regulatory-control rows for HIPAA/FINRA/PCI/GDPR/SOX projects
- [ ] Data steward is at minimum C on every data-model row
- [ ] Architecture is split into security and integration columns — not collapsed
- [ ] Phase and version are stamped on the matrix
- [ ] Sponsor + steerco review date is captured, next review date is scheduled

---

## Salesforce-Specific Gotchas

Non-obvious project-governance behaviors that cause real production problems:

1. **A migrated to the consulting partner and never transferred back.** During implementation the SI's lead architect carries A on integration and security because they own the design. If A does not transfer to a named customer employee before hypercare ends, the customer has no decision-maker post-go-live and every change request blocks until a partner is re-engaged.

2. **Compliance officer demoted to C on regulated data.** Project teams find compliance's review cycle slow and quietly leave them as C. The system ships, audit fires, and the gap forces a remediation project that costs more than the original build.

3. **Single-sponsor RACI on an M&A.** Naming one sponsor too early disenfranchises the other org's stakeholders. They disengage from steerco, requirements drift, and the merger fails to consolidate. Use a steerco-as-A pattern until the legal merger closes.

4. **AppExchange owner missing from the matrix.** Decisions touching a managed-package namespace (Conga, DocuSign, CPQ, FSL, NPSP) require the package owner's input — they know what the next package release will break. Omitting them produces decisions that get reversed by the next package upgrade.

5. **Escalation paths without time-boxes.** "Escalate to sponsor if blocked" with no clock means the team waits indefinitely for the A to decide. A 3–5 business-day time-box should be the default, with shorter for security and longer for license-tier decisions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| RACI matrix (markdown) | One row per decision category, one column per stakeholder role; cells contain R/A/C/I |
| RACI matrix (JSON) | Machine-readable mirror of the markdown for `check_raci.py` and downstream agent consumption |
| Escalation rule table | One row per A cell; columns: trigger, target, time-box |
| Refusal-code-to-stakeholder map | Mapping from `REFUSAL_*` codes to the named A who should be paged |
| Review log | Sponsor / steerco review date, attendees, version stamp, next review date |

---

## Related Skills

- admin/requirements-gathering-for-sf — use first, to identify the stakeholders before assigning their authority
- admin/change-management-and-deployment — covers the CAB operating model that the RACI references
- admin/change-management-and-training — covers end-user adoption, which is downstream of the RACI
- admin/permission-set-architecture — covers the technical authority model for permission set assignment
- admin/sandbox-strategy — feeds the deployment-row decisions on which sandboxes a change traverses
- standards/decision-trees/automation-selection.md — the tree the automation-tier A cell consults
- standards/decision-trees/sharing-selection.md — the tree the security-model A cell consults
- standards/decision-trees/integration-pattern-selection.md — the tree the integration-boundary A cell consults
- agents/_shared/REFUSAL_CODES.md — the refusal-code enum the matrix maps to
