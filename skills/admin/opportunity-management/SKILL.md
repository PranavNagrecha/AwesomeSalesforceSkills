---
name: opportunity-management
description: "Configuring Salesforce opportunity management: sales stages, sales processes, opportunity record types, Path configuration, opportunity teams, opportunity splits, and forecasting categories. Use when setting up or restructuring the opportunity lifecycle for Sales Cloud. NOT for Collaborative Forecasts setup (use collaborative-forecasts skill). NOT for CPQ pricing or product configuration (use Revenue Cloud skills). NOT for territory-based forecasting alignment (use enterprise-territory-management skill)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "How do I set up opportunity stages and sales processes for different business units?"
  - "My forecast categories are wrong and I need to fix how stages map to Pipeline vs Commit"
  - "We want to split opportunity revenue between two reps — how do we configure opportunity splits?"
  - "I need to add Path guidance to Opportunity so reps see key fields at each stage"
  - "How do I enable team selling so multiple reps can collaborate on a deal?"
tags:
  - opportunities
  - sales-process
  - stages
  - forecasting
  - opportunity-splits
  - path
  - sales-cloud
  - forecast-categories
  - record-types
inputs:
  - "List of sales stages needed per business motion (e.g., new logo vs. renewal)"
  - "Whether splits are required and which type (revenue vs. overlay)"
  - "Forecast types needed and whether Collaborative Forecasting is enabled"
  - "Existing record types and which sales process should apply to each"
outputs:
  - "Ordered configuration checklist for stages, sales processes, record types, and Path"
  - "Decision guidance on whether to use revenue vs. overlay splits"
  - "Validation rules approach for enforcing stage progression"
  - "Forecast category mapping for each stage"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Opportunity Management

This skill activates when configuring or restructuring the opportunity lifecycle in Sales Cloud: defining stages, building sales processes, assigning them to record types, adding Path guidance, enabling team selling and splits, and aligning stages to forecast categories. The configuration chain has a strict dependency order — skipping or reversing steps causes broken picklists, forecast gaps, or data integrity issues.

---

## Before Starting

Gather this context before working on anything in this domain:

- Know whether the org uses Collaborative Forecasting and which forecast object it uses (Opportunity, Opportunity Product, Opportunity Split, or Product Schedule) — this determines how splits feed forecasts.
- Confirm whether Opportunity Splits has ever been enabled. Splits cannot be disabled once any split data exists, and the setup order relative to Team Selling is non-negotiable.
- Identify how many distinct sales motions exist (e.g., direct new logo, renewal, channel partner) — each may need its own Sales Process, which means its own record type and stage subset.
- Check how many custom forecast types the org already has. The default limit is 4 custom forecast types; raising it to 7 requires a Support case.

---

## Core Concepts

### Stage Picklist Values and Their Platform-Level Properties

Every Opportunity Stage is a global picklist value that carries four platform-enforced fields: `IsClosed` (boolean), `IsWon` (boolean), `Probability` (default, overridable per record), and `ForecastCategoryName`. These are set at the global picklist level in Setup > Opportunity Stages and are NOT overridable per sales process or record type.

`ForecastCategoryName` maps to exactly five fixed platform values: Pipeline, Best Case, Commit, Closed, and Omitted. These labels cannot be renamed. Stages mapped to `Omitted` are excluded from all forecast rollups. Stages mapped to `Closed` must also have `IsClosed = true`.

Deleting a stage picklist value while records still use it does not produce a validation error at deletion time — it silently corrupts existing records by leaving them with a blank Stage field. Always reassign records before deleting a stage value.

### Sales Processes and the Configuration Chain

A Sales Process is a filtered view of the global Stage picklist. It controls which stage values are available on a record type. The dependency chain must be followed in this exact order:

1. Define all Stage picklist values globally (with IsWon, IsClosed, Probability, ForecastCategoryName set correctly).
2. Create Sales Processes in Setup > Sales Processes, selecting only the stages relevant to that business motion.
3. Assign a Sales Process to each Opportunity Record Type.
4. Configure Path Settings on top of a record type's active stages.

A stage not assigned to a Sales Process cannot appear in any record type or Path built from that process. Path Settings add guidance and key fields per stage but do NOT enforce stage progression — enforcement requires separate validation rules.

### Path Configuration

Path is a visual component layered on top of a record type's available stages. It provides guidance text and up to 5 key fields per stage to prompt rep behavior. Path is configured in Setup > Path Settings and requires the record type and its sales process to be active first.

Path does not prevent reps from jumping stages. If stage progression must be enforced (e.g., Close Date cannot be blank until Proposal stage), use a validation rule with `ISPICKVAL(StageName, 'Proposal') && ISBLANK(CloseDate)` logic. Path and validation rules are complementary — Path guides, validation rules enforce.

### Team Selling and Opportunity Splits

Team Selling must be enabled before Opportunity Splits is enabled — this is a hard platform dependency. Once Team Selling is on, Sales Team member roles become available on records.

Opportunity Splits has two types:
- **Revenue splits**: Must total exactly 100%. These feed revenue-based forecast types.
- **Overlay splits**: Can exceed 100% in total. These feed overlay forecast types (e.g., overlay SE credit). Overlay split totals are not validated against 100%.

Splits cannot be disabled after split data has been saved. This is a one-way door. Before enabling splits in production, confirm the business process permanently requires them.

---

## Common Patterns

### Multi-Motion Sales Process Setup

**When to use:** The org serves different buyer motions (e.g., new logo, renewal, channel partner) that move through different stage sequences.

**How it works:**
1. Define all stage values globally in Setup > Opportunity Stages. Set ForecastCategoryName and IsClosed/IsWon flags on every stage.
2. Create a separate Sales Process for each motion (e.g., "New Logo Process", "Renewal Process"). Assign only the relevant stages to each.
3. Create or update Opportunity Record Types. Assign one Sales Process per record type.
4. Build Path Settings for each record type individually. Path is configured per record type, not per sales process.
5. Write validation rules that reference `RecordType.DeveloperName` to enforce stage-specific field requirements per motion.

**Why not a single process:** A single catch-all process forces reps through irrelevant stages and pollutes forecast data with stages that don't match the motion's pipeline semantics.

### Revenue Split + Forecast Type Alignment

**When to use:** Multiple reps share credit on deals and the business needs their individual quotas reflected in forecasting.

**How it works:**
1. Enable Team Selling in Setup > Opportunity Team Settings.
2. Enable Opportunity Splits and configure split types (revenue and/or overlay).
3. In Collaborative Forecasting Setup, choose "Opportunity Splits" as the forecast object for revenue-credit forecast types.
4. Create a separate forecast type for overlay splits if overlay credit tracking is needed.
5. Assign forecast types to user profiles via Permission Sets or Profile-based Forecast Type access.

**Why not use Opportunity Amount:** Amount-based forecasting double-counts when multiple reps appear in splits. Split-based forecasting credits each rep's share.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Two business motions with different stages | Separate Sales Processes + Record Types | Prevents stage contamination across motions; keeps forecast rollups clean |
| Need to guide reps on key fields per stage | Configure Path Settings | Path provides inline guidance without requiring custom page layouts per stage |
| Need to prevent reps from skipping required stages | Add Validation Rules (not Path) | Path is visual only — it does not block saves |
| Multiple reps need credit on a deal | Enable Revenue Splits | Splits feed forecast rollups per rep; Amount-only forecasting double-counts |
| Overlay team (SEs, pre-sales) need separate credit | Enable Overlay Splits + separate forecast type | Overlay totals can exceed 100%; they feed a distinct forecast type without affecting quota |
| Stage no longer used | Reassign all records, then deactivate — never delete while records use it | Deletion silently blanks Stage on existing records |
| Forecast category label needs renaming | This cannot be done — ForecastCategoryName values are platform-fixed | The five values (Pipeline, Best Case, Commit, Closed, Omitted) cannot be renamed |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Audit existing Stage picklist values in Setup > Opportunity Stages. Confirm every stage has IsClosed, IsWon, Probability, and ForecastCategoryName set correctly. Flag any stage mapped to a blank or unexpected forecast category.
2. Confirm how many Sales Processes the org needs — one per distinct sales motion. Create or update Sales Processes, assigning only the stage values relevant to each motion. Verify that no required stage is missing from a process before assigning to a record type.
3. Assign each Opportunity Record Type to exactly one Sales Process. Do not leave record types on the default process unless that process covers all required stages for that type.
4. Configure Path Settings for each active record type. Add guidance text and up to 5 key fields per stage. Do not rely on Path to enforce progression — note any progression rules that must be implemented as validation rules.
5. If splits are required: enable Team Selling first, then enable Opportunity Splits. Select split types (revenue and/or overlay). Confirm this decision with business stakeholders — splits cannot be disabled once data exists.
6. Verify Collaborative Forecasting forecast types reference the correct source object (Opportunity vs. Split). Check that the number of custom forecast types does not exceed the org's limit (default 4, max 7 with Support).
7. Run the skill-local checker: `python3 skills/admin/opportunity-management/scripts/check_opportunity_management.py --manifest-dir path/to/metadata`. Review all flagged issues before deploying.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every Stage picklist value has a non-blank ForecastCategoryName set to one of the five fixed platform values
- [ ] Every Stage with IsWon=true also has IsClosed=true; every Closed stage has IsClosed=true
- [ ] Each Sales Process contains only stages valid for that business motion; no stages are missing
- [ ] Each Opportunity Record Type is assigned exactly one Sales Process
- [ ] Path Settings are active for each record type where guidance is needed; key fields per stage are configured
- [ ] Team Selling was enabled BEFORE Opportunity Splits if splits are in use
- [ ] Revenue splits total exactly 100% per opportunity (platform-enforced); overlay splits are not constrained to 100%
- [ ] Forecast types reference the correct source object and do not exceed the org's custom type limit
- [ ] No Stage picklist value with active records has been deleted; deactivation was used instead
- [ ] Validation rules enforcing stage progression are in place and tested; Path alone is not treated as enforcement

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Deleting a Stage value corrupts active records silently** — When a Stage picklist value is deleted while Opportunity records still use it, Salesforce does not block the deletion and does not reassign those records. The Stage field on affected records becomes blank, breaking forecast rollups and any validation rules that reference StageName. Always use the "Replace" action to move records to a new stage before deleting, or deactivate the value instead.

2. **ForecastCategoryName values are platform-fixed and cannot be renamed** — The five values (Pipeline, Best Case, Commit, Closed, Omitted) are hardcoded in the platform. Attempts to rename them via picklist metadata or the UI will fail silently or error. Org-specific category labels must be communicated through field help text, Path guidance, or documentation — not by renaming the platform values.

3. **Splits cannot be disabled once any split record exists** — Opportunity Splits is a one-way door. Once enabled and any split data is saved, the feature cannot be turned off. This also means the split type configuration (revenue vs. overlay) becomes permanent for the types that have data. Evaluate the business requirement thoroughly before enabling in production.

4. **Team Selling must be enabled before Opportunity Splits** — The platform dependency is hard. Attempting to enable Splits without Team Selling enabled first results in an error. The reverse (disabling Team Selling after Splits is on) is also blocked once split data exists.

5. **Path enforces nothing** — A common misconception is that configuring Path on a stage makes that stage required or orderly. Path is a visual guidance layer only. Reps can save a record at any stage regardless of Path configuration. Stage progression enforcement requires validation rules.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Stage audit report | Table of all Stage values with their IsClosed, IsWon, Probability, and ForecastCategoryName values — used to verify correct forecast rollup mapping |
| Sales Process assignment matrix | Map of each Record Type to its assigned Sales Process and the stages that process exposes — used to confirm no stages are missing per motion |
| Checker output | Output of `check_opportunity_management.py` listing metadata issues found in the deployed manifest |

---

## Related Skills

- enterprise-territory-management — use alongside when territory-based opportunity assignment and territory forecast rollups are required
- path-and-guidance — use for deep Path configuration patterns including conditional field visibility per stage
- record-type-strategy-at-scale — use when deciding how many record types the org needs and how to manage picklist complexity across them
- picklist-and-value-sets — use when managing the global Stage picklist values and dependent picklist relationships
