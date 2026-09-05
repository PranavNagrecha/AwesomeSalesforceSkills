---
name: stakeholder-raci-for-sf-projects
description: "Use this skill when building, reviewing, or refreshing a RACI (Responsible / Accountable / Consulted / Informed) matrix for a Salesforce project so that every Salesforce-specific decision — data model change, automation tier choice, security model, integration boundary, deployment, license/edition — has exactly one accountable owner and a documented escalation path that downstream agents can route to. Trigger keywords: RACI matrix salesforce project, stakeholder authority salesforce, escalation path salesforce decisions, who approves data model change, salesforce decision rights, REFUSAL_NEEDS_HUMAN_REVIEW routing. NOT for the change advisory board operating model itself (use admin/change-management-and-deployment). NOT for end-user training rollout plans (use admin/change-management-and-training). NOT for the technical mechanics of permission set assignment authority (use admin/permission-set-architecture). NOT for pure stakeholder requirements elicitation (use admin/requirements-gathering-for-sf). More trigger keywords: who approves a sandbox refresh, who signs off a data load, release update activation owner, delegated admin authority vs RACI, multi-org decision rights, escalation time-box."
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
  - "who approves a sandbox refresh in Salesforce"
  - "who signs off a Salesforce data load before it runs"
  - "nobody owns activating our Salesforce release updates"
  - "delegated admin can assign permission sets we never approved"
  - "same role different person in each org multi-org governance"
  - "our escalation path has no time-box and decisions stall"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
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

## Questions to Ask Before Configuring

Ask these before drafting a single cell. Each one exists because a specific failure recurs — the
matching gotcha is named in the last column so you can see what the answer is protecting you from.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who loses something when the sandbox is refreshed, and who schedules it?" | A refresh replaces the org; the person who runs it is rarely the person whose UAT evidence or seeded data disappears | Separate A (data owner) and R (release manager) on the refresh row, with a blocking trigger — `gotchas.md` §9 |
| "Who signs off a data load — the person who runs the tool, or the person who owns the records?" | Hard-deleted records cannot be recovered from the Recycle Bin, and a failed bulk job leaves a partial state someone must adjudicate | An A on the data owner and an escalation trigger on hard delete and row-count overrun — `gotchas.md` §13 |
| "Who decides when we activate a Release Update, and against which enforcement release?" | Release Updates carry an availability release and an enforcement release; unowned, the platform activates on its date | A release-update row with A on the release manager and a time-box measured in releases — `gotchas.md` §12 |
| "Which delegate groups exist today, and do they match what this matrix says about permissions?" | Delegated administration is the decision-rights model made deployable — the org grants what the metadata says, not what the deck says | A retrieve-and-diff step at each phase review — `gotchas.md` §14 |
| "Is 'the Salesforce admin' one column or several roles one person happens to fill?" | One column means one bottleneck and no successor; the platform itself splits admin authority | A register that records the double-hatting instead of merging the columns — `gotchas.md` §10 |
| "Which running integrations does this org already have, and who owns each one?" | API allocations and concurrency limits are org-wide and shared; an unlisted integration can fail your rehearsed load | Named owners for existing integrations as C on the integration row — `gotchas.md` §11 |
| "If this is a multi-org programme, does each role mean the same person in every org?" | Roles, delegate groups, and release managers are org-scoped; one column hides two different authorities | Org-scoped columns (`RM_A`, `RM_B`) and a steerco A on cross-org decisions — `gotchas.md` §15 |

What a proper matrix adds over just naming an owner per workstream: every irreversible Salesforce
action — refresh, load, hotfix, release-update activation — has exactly one named person who can
authorise it, a clock that fires when they do not, and a decision log an auditor can read a year later.

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

### The Ten Required Activity Rows

The six categories above are how you *think* about the surface. The rows you actually write are the
ten activities below — the ones that are irreversible, expensive to reverse, or driven by a date
Salesforce sets rather than one you set. `scripts/check_raci.py` requires every slug to appear at
least once; a missing slug is an error, because a required decision with no row is a decision with no
owner.

| Activity slug | Category | Typical A | Executed by |
|---|---|---|---|
| `data-model-change` | Data model | Data steward or process owner | `agents/object-designer/AGENT.md`, `agents/field-impact-analyzer/AGENT.md` |
| `sharing-model-change` | Security | Security architect | `agents/access-path-explainer/AGENT.md` |
| `permission-set-change` | Security | CRM admin lead | `agents/permission-set-architect/AGENT.md` |
| `integration-change` | Integration | Integration architect | `agents/integration-catalog-builder/AGENT.md` |
| `release-go-no-go` | Deployment | Business sponsor | `agents/release-readiness-reviewer/AGENT.md` |
| `sandbox-refresh-approval` | Deployment | Data owner (not the refresher) | `agents/sandbox-strategy-designer/AGENT.md` |
| `production-hotfix` | Deployment | Release manager | `agents/deployment-risk-scorer/AGENT.md`, `agents/changeset-builder/AGENT.md` |
| `data-load-approval` | Data model | Data steward | `agents/data-loader-pre-flight/AGENT.md`, `agents/data-migration-reconciler/AGENT.md` |
| `release-update-activation` | Deployment | Release manager | `agents/change-impact-planner/AGENT.md`, `agents/org-health-assessor-v2/AGENT.md` |
| `seasonal-release-preview` | Deployment | Release manager | `agents/release-train-planner/AGENT.md` |

Sub-rows share a slug: a regulated programme writes two `data-model-change` rows (regulated data and
everything else) with different As. The automation-tier and license/edition categories stay as
optional extra rows — they are decisions, but they are reversible, so they do not carry the same
"nobody owns this and the platform is about to act" risk the ten do. A filled version of all ten,
with escalation rules and the executing agent per row, is in `references/worked-examples.md`.

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

| Letter | Meaning |
|---|---|
| R (Responsible) | Does the work. There can be many Rs per row. |
| A (Accountable) | Owns the outcome and is the single decision-maker. **Exactly one A per row.** This is the load-bearing rule of any RACI; multiple As mean nobody is accountable. |
| C (Consulted) | Two-way conversation before the decision is made. Their input is required, not optional. |
| I (Informed) | One-way notification after the decision is made. |

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

1. **Fill the intake sheet and build the register.** Copy
   `templates/stakeholder-raci-for-sf-projects-template.md`; record phase, org topology, regulatory
   overlay, managed packages, delegate groups already in the org, and the partner's hypercare exit
   date, working the `## Questions to Ask Before Configuring` table into it. Then name a person for
   every roster role with org unit, Salesforce persona, user licence, and decision rights — the six
   columns in `references/worked-examples.md` §1. An unnamed role is a project risk to escalate, not
   a placeholder to fill later.
2. **Write the ten activity rows.** Copy `templates/raci-matrix.md`, keep the ten required slugs, and
   add sub-rows only where a category needs splitting. Apply the one-A rule, the no-A-on-a-C rule, and
   the every-row-has-an-R rule as you fill cells.
3. **Attach an escalation rule to every A, and an escalation path to the programme.** Trigger, target,
   time-box per row; level, forum, chair, time-box per escalation level. `references/gotchas.md` §4
   is why the time-box is not optional.
4. **Map each R to its executor.** Fill `executed_by` with the repo path of the agent, skill, or
   decision tree that carries out the row — see the table in `## Core Concepts` and
   `references/worked-examples.md` §5.
5. **Lint the artefact.** Run
   `python3 scripts/check_raci.py --file <path>/raci.yaml --repo-root <repo> --strict`. Errors are
   structural (missing A, missing R, missing required activity, missing escalation, unresolved
   `executed_by`); fix them before circulating. Warnings are judgement calls — read them, then decide.
6. **Reconcile the matrix against the org.** Retrieve the delegate groups and diff them against the
   permission row (`references/worked-examples.md` §6). A difference is a decision made outside the
   governance path.
7. **Review, version-lock, log.** Capture the sponsor sign-off date, the next review date, and the
   phase in the artefact header. Record decisions as they are made in the `decision_log` shape — the
   next phase gets a new version, not an in-place edit.

## Review Checklist

Run through these before publishing the matrix:

- [ ] All ten required activity slugs have a row (`check_raci.py` errors on a missing one)
- [ ] Every row has exactly one A
- [ ] No row has A on a C role
- [ ] Every row has at least one R
- [ ] Every R/A/C/I value is from the enum (R, A, C, I) — no blanks, no commentary
- [ ] Every A cell has a written escalation rule with trigger + target + time-box
- [ ] The escalation target on each row is someone other than that row's A
- [ ] A programme-level `escalation_path` exists with level, forum, chair, and time-box per level
- [ ] Every `executed_by` path resolves to a real agent, skill, or decision tree in the repo
- [ ] Delegate groups in the org have been retrieved and diffed against the permission row
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


Seven more — the sandbox refresh approved by someone who does not own the data in it, "the Salesforce
admin" as A for everything, integrations whose owners are outside the matrix, release-update
activation owned by nobody, the data load signed off by the tool operator instead of the record owner,
delegate groups that contradict the permission row, and one role meaning two different people in a
multi-org programme — are in `references/gotchas.md` §9–§15, each with the platform behaviour that
makes it bite.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Stakeholder register | One row per role: named person, org unit, Salesforce persona, user licence, decision rights |
| RACI matrix (markdown) | The circulated view — one row per activity, one column per stakeholder role; cells contain R/A/C/I |
| RACI matrix (YAML) | The artefact of record, linted by `scripts/check_raci.py`. JSON with the same keys is accepted |
| Escalation rules + escalation path | Per-row trigger / target / time-box, plus programme-level levels, forums, chairs |
| R-to-executor map | `executed_by` per row: the agent, skill, or decision tree that carries out the work |
| Refusal-code-to-stakeholder map | Mapping from `REFUSAL_*` codes to the named A who should be paged |
| Decision log | Per decision: date, activity, decision, decided by, consulted, alternatives rejected, reversal cost, evidence |
| Review log | Sponsor / steerco review date, attendees, version stamp, next review date |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You need the filled artefacts — register, ten-row matrix in markdown and YAML, escalation path, decision log, R-to-executor map, and the DelegateGroup / CustomMetadata XML that makes the matrix deployable |
| `references/examples.md` | You need a matrix shaped for a specific programme type — greenfield, regulated (HIPAA), or M&A multi-org — or the sponsor-as-universal-A anti-pattern with the linter output |
| `references/gotchas.md` | Before publishing, and any time a cell feels obvious — 15 failure modes with what happens / when it occurs / how to avoid |
| `references/well-architected.md` | You are justifying the matrix to an architecture review, or need the pillar mapping and the source list |
| `references/llm-anti-patterns.md` | An AI assistant is generating or reviewing the matrix — the seven ways it goes wrong |
| `scripts/check_raci.py` | Every time the artefact changes: `--file <raci.yaml> --repo-root <repo> --strict` |
| `templates/raci-matrix.md` | You are producing the deliverable — the matrix, escalation, refusal map, and YAML shape to fill |
| `templates/stakeholder-raci-for-sf-projects-template.md` | You are starting an engagement — the intake sheet that captures context before any cell is filled |

---

## Related Skills

- admin/requirements-gathering-for-sf — use first, to identify the stakeholders before assigning their authority
- admin/change-management-and-deployment — covers the CAB operating model that the RACI references
- admin/change-management-and-training — covers end-user adoption, which is downstream of the RACI
- admin/permission-set-architecture — covers the technical authority model for permission set assignment
- admin/delegated-administration — the permission row made concrete: the delegate group that either matches this matrix or contradicts it
- devops/release-management — the release train the go/no-go, hotfix, release-update, and preview rows sit inside
- admin/sandbox-strategy — feeds the deployment-row decisions on which sandboxes a change traverses
- standards/decision-trees/automation-selection.md — the tree the automation-tier A cell consults
- standards/decision-trees/sharing-selection.md — the tree the security-model A cell consults
- standards/decision-trees/integration-pattern-selection.md — the tree the integration-boundary A cell consults
- agents/_shared/REFUSAL_CODES.md — the refusal-code enum the matrix maps to
- agents/_shared/AGENT_CONTRACT.md — why an agent's Citations block and confidence score are usable as decision-log evidence
- agents/org-health-assessor-v2/AGENT.md — reports the pending release updates and org-level findings the matrix must assign owners to
- agents/release-readiness-reviewer/AGENT.md — produces the evidence the go/no-go A signs
