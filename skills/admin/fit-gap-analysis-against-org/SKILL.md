---
name: fit-gap-analysis-against-org
description: "Use when scoring a list of business or solution requirements against the *actual* capabilities of a specific Salesforce org so each row can be classified Standard / Configuration / Low-Code / Custom / Unfit, given an effort tier (S/M/L/XL), a risk tag, and an AppExchange suggestion when applicable. Trigger keywords: fit gap salesforce requirements, score requirements against salesforce capabilities, salesforce capability matrix, classify requirement as standard config custom, fit-gap effort tier, AppExchange alternative for requirement. NOT for requirements elicitation (use admin/requirements-gathering-for-sf). NOT for architecture decisions on the GAP rows (use architect/solution-design-patterns and standards/decision-trees/). NOT for license or edition selection (use architect/license-optimization-strategy and architect/org-edition-and-feature-licensing). NOT for OmniStudio-specific fit-gap (use architect/omnistudio-vs-standard-decision)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Scalability
  - Reliability
triggers:
  - "fit gap salesforce requirements against an existing org"
  - "score requirements against salesforce capabilities standard config custom"
  - "build a salesforce capability matrix for a requirements backlog"
  - "classify each requirement as standard, configuration, low-code, custom, or unfit"
  - "estimate effort tier S/M/L/XL for each salesforce requirement"
  - "find AppExchange alternative for requirements salesforce cannot satisfy"
  - "decide which fit-gap rows go to which downstream agent (object designer, flow builder, apex builder)"
tags:
  - fit-gap-analysis
  - capability-matrix
  - requirement-scoring
  - effort-estimation
  - risk-tagging
  - appexchange-evaluation
  - handoff-routing
  - admin
inputs:
  - "Requirements list (one row per requirement, normalized: id, title, description, source persona)"
  - "Target org context: edition, enabled features, installed packages, license SKUs and counts"
  - "Existing automation inventory on the in-scope objects (flows, triggers, validation rules)"
  - "Constraints from the customer: timeline, budget tier, in-house developer availability"
  - "AppExchange policy: is the customer open to paid managed packages, or 100% in-house only"
outputs:
  - "Fit-gap matrix with one row per requirement, scored Standard / Configuration / Low-Code / Custom / Unfit"
  - "Effort tier (S / M / L / XL) per row using the formula in this skill"
  - "Risk tag per row from the canonical taxonomy (license-blocker, data-skew, governance, customization-debt, no-AppExchange-equivalent)"
  - "Recommended downstream agent and skill citations for each row (object-designer, flow-builder, apex-builder, architecture-escalation)"
  - "AppExchange alternatives list for any row where a managed package can replace custom build"
  - "Architecture-escalation note for every Unfit row, naming the decision tree the issue belongs in"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Fit-Gap Analysis Against Org

This skill activates after requirements have been gathered and the team needs to convert that backlog into a build plan that respects the *actual* org's edition, licenses, installed packages, and existing automation. It produces a deterministic per-row classification, effort tier, risk tag, and downstream-agent handoff. It does NOT elicit requirements (handled by `admin/requirements-gathering-for-sf`) and does NOT pick the technology to use for the GAP cases (handled by `architect/solution-design-patterns` plus `standards/decision-trees/`).

The output of this skill is the *routing manifest* for the rest of the build pipeline: Standard and Configuration rows go to `agents/object-designer/AGENT.md`, Low-Code rows to `agents/flow-builder/AGENT.md`, Custom rows to `agents/apex-builder/AGENT.md`, and Unfit rows trigger an architecture-escalation review.

---

## Before Starting

Gather this context before scoring a single row:

- **Org edition and enabled features.** A "Standard" row in Enterprise Edition becomes a "Configuration" or even an "Unfit" row in Professional Edition. Probe the org with `Setup → Company Information → Organization Edition` and `Setup → Object Manager` to confirm features (e.g. Forecasting, Knowledge, Service Cloud Voice) are actually licensed and enabled.
- **Installed AppExchange packages.** A managed package may already deliver 70% of a "Custom" row's behavior. Run `Setup → Installed Packages` and reconcile against the requirement before classifying as Custom.
- **License SKU counts.** A Standard feature with a per-user license cap (e.g. CPQ user, Service Cloud user, Industry Cloud user) becomes a GAP for any user persona that does not have that license. Check `Setup → Company Information → User Licenses + Permission Set Licenses` and cross-reference with the requirement's persona.
- **Existing automation on the in-scope objects.** A new requirement that conflicts with an existing trigger or record-triggered Flow is not free to build, regardless of classification. Inventory `Setup → Process Automation → Flows` and `Object Manager → Triggers` per in-scope sObject.
- **AppExchange policy.** Some customers refuse paid managed packages on principle. That single constraint can force a row from "Standard via package" to "Custom build" — and changes the effort tier dramatically.

---

## Core Concepts

### The 5-Tier Classification Rubric

Every row in the fit-gap matrix gets exactly one tier. The tiers are an ordered ladder — pick the *highest* (least invasive) tier that genuinely satisfies the requirement, given the org's actual configuration.

| Tier | Definition | Examples |
|---|---|---|
| **Standard** | Salesforce delivers this *out of the box* in the org's licensed edition with no configuration beyond enabling the feature or assigning a permission. | Account/Contact relationships, standard Case escalation milestones in Service Cloud, Lightning Experience navigation. |
| **Configuration** | Point-and-click only — no formula language, no Flow, no code. Requires admin work in Setup but no logic authoring. | Creating custom fields, setting up record types and page layouts, defining standard list views, configuring email templates from Setup. |
| **Low-Code** | Requires Flow, Dynamic Forms, formula fields, validation rules, or other declarative authoring with conditional logic — but no Apex, no LWC, no callouts. | Record-Triggered Flow that updates related records on opportunity close, formula field rolling up SLA breaches, validation rule blocking save when picklist combo is invalid. |
| **Custom** | Requires Apex, LWC, external integration, or any combination thereof. | Apex trigger handler enforcing a multi-object cascade rule, LWC dashboard pulling external KPIs, REST callout to a billing system on opportunity close. |
| **Unfit** | Salesforce *cannot* satisfy this requirement without violating a platform constraint, license cap, or governance rule — or the requirement belongs on a different platform entirely. | A real-time analytics requirement that exceeds Big Object query limits and belongs in Tableau / CRM Analytics / a data warehouse, an ETL pipeline that belongs in MuleSoft, a hard requirement for sub-100ms cross-org sync. |

### The Effort Tier Formula (S / M / L / XL)

Effort is *not* the same as classification. A Custom row can be Small if it is an isolated trigger; a Configuration row can be Large if it touches 30 page layouts and 12 record types. Use the formula:

```
effort = base(tier) + scope_multiplier + risk_multiplier
```

| Component | Value |
|---|---|
| `base(Standard)` | S |
| `base(Configuration)` | S |
| `base(Low-Code)` | M |
| `base(Custom)` | L |
| `base(Unfit)` | XL (because XL means "stop building until architecture review resolves it") |
| `scope_multiplier: +1 tier` | If the row touches more than 3 sObjects, more than 5 page layouts, or more than 1 user persona class. |
| `risk_multiplier: +1 tier` | If the row carries any risk tag from the taxonomy below. |

Cap at XL. Round S+0 → S, S+1 → M, S+2 → L, S+3 → XL.

### The Risk-Tag Taxonomy

Every row that has *any* of the following is tagged. A row may carry multiple tags; the matrix lists them all.

| Tag | Meaning | Example |
|---|---|---|
| **license-blocker** | The requirement's persona does not have a license SKU that includes the feature, or it requires a license tier the customer hasn't bought. | "Field Service technicians need Knowledge access" but the org has no Knowledge user licenses. |
| **data-skew** | The implementation will create account-data-skew, ownership-skew, or lookup-skew at expected volumes. | A single "House Account" pattern routing all unassigned leads to one owner. |
| **governance** | The requirement violates the org's existing governance standards (naming conventions, deployment policy, security posture). | A Custom row that requires turning off a Restriction Rule. |
| **customization-debt** | The requirement adds Apex/LWC where a managed package or future Salesforce roadmap feature will replace it within 18 months. | Building a custom forecasting overlay six months before Forecasting 2.0 GA. |
| **no-AppExchange-equivalent** | The customer policy is "AppExchange first" but no listed package solves the requirement, *or* the package is unmaintained / deprecated. | Vertical-specific Knowledge workflow with no current AppExchange package. |

### The Canonical Handoff Row Shape

The matrix is produced as both a markdown table (for humans) and a JSON list (for downstream agents). Each JSON row is shaped:

```json
{
  "requirement_id": "REQ-042",
  "title": "Auto-route inbound leads by region within 5 minutes",
  "tier": "Low-Code",
  "effort": "M",
  "risk_tag": ["governance"],
  "recommended_agents": ["flow-builder"],
  "recommended_skills": [
    "admin/lead-routing-rules-design",
    "flow/record-triggered-flow-patterns"
  ],
  "appexchange_alternatives": [],
  "decision_tree_branch": null,
  "notes": "Requires re-using existing assignment rule pattern; no Apex needed."
}
```

For Unfit rows, `recommended_agents` is `["architecture-escalation"]` and `decision_tree_branch` *must* point to the relevant tree (e.g. `standards/decision-trees/integration-pattern-selection.md#etl-vs-realtime`).

---

## Common Patterns

### Pattern 1: Greenfield Sales Cloud Implementation

**When to use:** New Sales Cloud org, ~15–40 requirements, mix of Standard and Low-Code expected.

**How it works:**

1. Probe the org's edition (typically Enterprise) and confirm Salesforce Inbox, Forecasting, Pardot/Account Engagement licensing.
2. Score each requirement; expect 50–60% Standard, 25–30% Low-Code, ~10% Custom, ~5% Unfit.
3. Hand Standard rows directly to `object-designer`; batch Low-Code rows to `flow-builder` per sObject; queue Custom rows for `apex-builder`.

**Why not the alternative:** Skipping the Configuration tier and lumping everything into "Standard" or "Custom" loses the ability to estimate effort. Configuration rows are the bulk of any greenfield admin's actual workload.

### Pattern 2: Service Cloud Expansion Onto an Existing Sales Cloud Org

**When to use:** Customer already has Sales Cloud, is adding Service Cloud.

**How it works:** Probe for Service Cloud user licenses, Knowledge enablement, Omni-Channel licensing. Many "Standard" Service Cloud features become license-blocker GAPs because the customer only bought Sales licenses.

**Why not the alternative:** Treating "Service Cloud features" as Standard without probing licenses is the single most common failure mode in fit-gap.

### Pattern 3: Vertical Cloud (FSC, Health Cloud, Industries) Project

**When to use:** Customer has Industries Cloud or vertical edition.

**How it works:** Vertical clouds ship managed packages that *re-classify* otherwise-Custom requirements into Standard. Always reconcile against the installed Industry packages first; many Custom rows collapse to Standard or Configuration.

---

## Decision Guidance

| Situation | Recommended Tier | Reason |
|---|---|---|
| Requirement asks for "automation" without specifying complexity | Default to Low-Code; promote to Custom only if Flow cannot satisfy it (per `automation-selection.md`) | Avoid the trap of "automation = Apex". |
| Requirement is delivered by an installed managed package | Standard (with note: "via {package-name}") | Managed packages count as Standard once installed and licensed. |
| Requirement needs a same-transaction HTTP callout | Custom | Flow cannot make synchronous after-save callouts. |
| Requirement persona lacks the required license SKU | Unfit + `license-blocker` tag | Cannot be classified Standard if the persona literally cannot access it. |
| Requirement is "real-time analytics across millions of records" | Unfit + escalation note pointing to CRM Analytics / data warehouse | Wrong-platform escape hatch. |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Intake the requirements list.** Confirm every row has a stable `requirement_id`, a title, a description, and a source persona. Reject incomplete rows back to `admin/requirements-gathering-for-sf` rather than guessing.
2. **Probe the target org.** Capture edition, enabled features, installed managed packages, license SKU counts per persona, and existing automation on the in-scope sObjects. Without this probe step the matrix is a guess, not a fit-gap.
3. **Classify each row into one of the five tiers** (Standard / Configuration / Low-Code / Custom / Unfit), using the rubric above. Pick the *highest* tier that genuinely satisfies the requirement given the org's actual state.
4. **Attach an effort tier** (S / M / L / XL) using the formula `base(tier) + scope_multiplier + risk_multiplier`. Cap at XL.
5. **Attach risk tag(s)** from the taxonomy: `license-blocker`, `data-skew`, `governance`, `customization-debt`, `no-AppExchange-equivalent`. Multiple tags are allowed.
6. **Hand off rows to downstream agents.** Standard + Configuration → `object-designer`; Low-Code → `flow-builder`; Custom → `apex-builder`. Populate `recommended_skills` per row using the skill IDs from `agents/_shared/SKILL_MAP.md`.
7. **Flag every Unfit row for architecture review.** Each Unfit row must cite the decision tree branch in `standards/decision-trees/` that the conflict belongs in, and must NOT proceed to a builder agent until that escalation closes.

---

## Review Checklist

Run through these before publishing a fit-gap matrix:

- [ ] Every row has exactly one tier from the 5-enum.
- [ ] Every row has an effort tier (S/M/L/XL).
- [ ] Every row has at least an empty `risk_tag` array; tags are drawn from the canonical taxonomy.
- [ ] Every Standard row is reconciled against the org's *actual* edition + license counts, not a generic Salesforce-Help description.
- [ ] Every Configuration row names the specific Setup areas that will be touched.
- [ ] Every Low-Code row has not silently absorbed something that needs Apex (callout, multi-object cascade, > 200-record bulk path).
- [ ] Every Custom row has `recommended_agents` populated.
- [ ] Every Unfit row has an architecture-escalation note and a `decision_tree_branch` reference.
- [ ] AppExchange alternatives have been searched for any row with `tier ∈ {Custom, Unfit}` *unless* the customer policy explicitly excludes managed packages.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real fit-gap mistakes:

1. **Process Builder is *not* still "Standard".** Process Builder is end-of-life. Any row classified as "still standard automation via PB" is wrong; route to Low-Code (Flow) or escalate.
2. **License caps invalidate Standard rows.** Out-of-the-box Knowledge access for a Service Cloud agent is Standard *only* if the agent has a Knowledge-enabled license. Otherwise it is `license-blocker` Unfit.
3. **Sandbox vs production feature deltas.** A feature enabled in a partial-copy sandbox is not necessarily live in production. Always probe the *target* org, not the sandbox the team has been demoing in.
4. **Permission cliffs turn Standard into Configuration.** A "Standard" feature that requires Setup Customize Application access for end users effectively becomes Configuration + a permission-set authoring task.
5. **AppExchange alternatives go stale.** A package listed on AppExchange may be unmaintained. Confirm last-update date and supported edition before counting it as Standard.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `templates/fit-gap-analysis-against-org-template.md` | Markdown table skeleton + canonical JSON row shape used for downstream-agent handoff. |
| `scripts/check_fit_gap_analysis_against_org.py` | Stdlib-only checker that validates a fit-gap matrix file: every row has a tier from the 5-enum, every Custom row has `recommended_agents`, every Unfit row has an architecture-escalation note, no row missing `risk_tag`. |

---

## Related Skills

- `admin/requirements-gathering-for-sf` — produces the input this skill consumes.
- `architect/solution-design-patterns` — owns the technology choice for any GAP row this skill flags.
- `architect/license-optimization-strategy` and `architect/org-edition-and-feature-licensing` — owns license + edition decisions when a row carries `license-blocker`.
- `architect/omnistudio-vs-standard-decision` — owns OmniStudio fit-gap when the project is OmniStudio-led.
- `standards/decision-trees/` — every Unfit row must cite a tree branch.
