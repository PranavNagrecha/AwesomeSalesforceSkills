---
name: einstein-discovery-setup
description: "Use this skill when an admin needs to create an Einstein Discovery story in CRM Analytics Studio, configure prediction definitions, deploy writeback fields, set up what-if analysis, or manage model refresh and activation. Trigger keywords: Einstein Discovery story, prediction definition, writeback field, CRM Analytics Studio, model refresh, what-if analysis, bulk scoring, prediction field, 1OR prefix. NOT for the Einstein Discovery Flow action or model-health monitoring in Model Manager — use admin/einstein-discovery-deployment. NOT for Einstein Prediction Builder, a separate product needing no CRM Analytics license — use agentforce/einstein-prediction-builder. NOT for programmatic scoring through the Connect REST API — use agentforce/einstein-discovery-development."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I create an Einstein Discovery story in CRM Analytics Studio?"
  - "Setting up prediction fields for Einstein Discovery on Opportunity records"
  - "Enabling Einstein Discovery recommendations on records using the admin wizard"
  - "How do I deploy an Einstein Discovery model so scores appear on page layouts?"
  - "Einstein Discovery writeback field is not showing up in reports or page layouts"
  - "move an Einstein Discovery prediction definition from sandbox to production"
  - "segment one prediction definition into separate models per region"
tags:
  - einstein-discovery-setup
  - einstein-discovery
  - crm-analytics
  - prediction-definition
  - writeback-field
  - story-creation
  - model-refresh
  - what-if-analysis
inputs:
  - "CRM Analytics license confirmed as provisioned in the org"
  - "Target Salesforce object and outcome field for the story (e.g., Opportunity.IsClosed)"
  - "Whether the use case requires Insights-only or Insights+Predictions (writeback to record fields)"
  - "Confirmation that admin has CRM Analytics Admin permission set or equivalent"
  - "List of explanatory variables (fields) available on the target object or related objects"
outputs:
  - "Guidance for completing the three-step story creation wizard in CRM Analytics Studio"
  - "Prediction definition configuration (1OR prefix, enabled status, target object mapping)"
  - "Writeback field setup instructions including field-level security assignment steps"
  - "Model refresh schedule and manual activation procedure"
  - "What-if analysis configuration guidance for surfacing recommendations on record pages"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
runtime_orphan: true
runtime_orphan_reason: "No run-time agent covers CRM Analytics / Einstein Discovery. This skill was previously listed in audit-router's Mandatory Reads, but no audit-router classifier routes to it and report_dashboard's own scope excludes CRM Analytics migration, so the citation was decorative rather than load-bearing. Removed 2026-08-14 rather than left as a citation an agent never honoured. Re-wire when a CRM Analytics agent exists."
---

# Einstein Discovery Setup

Use this skill when an admin configures Einstein Discovery: creating stories, deploying prediction definitions, writing predictions back to Salesforce fields, enabling improvements for what-if analysis, and managing model refresh and activation. It covers the admin path and the metadata that carries a prediction definition between orgs. For programmatic scoring and REST endpoints, use `agentforce/einstein-discovery-development`.

Grounding note: the Einstein Discovery admin guide pages are on help.salesforce.com, which did not fetch for this pass, and the Einstein Discovery REST API guide did not fetch either. The grounded source here is the Metadata API Developer Guide's `DiscoveryAIModel`, `DiscoveryGoal`, and `DiscoveryStory` types. Wizard and UI behavior carried from earlier versions of this skill is marked UNVERIFIED where it is stated as fact.

---

## Before Starting

- **CRM Analytics license.** Einstein Discovery requires a CRM Analytics license; Einstein Prediction Builder does not. The Analytics Platform Setup Guide lists Einstein Predictions as a separately purchased capability alongside CRM Analytics Growth and Plus.
- **What a prediction definition is.** In metadata it is a `DiscoveryGoal` (Package Manager label "Discovery Prediction"): "a container object in Einstein Discovery that is associated with one or more deployed models". It names the Salesforce object (`subscribedEntity`), the outcome, the deployed models, and the writeback field (`pushbackField`).
- **Segmented models.** A prediction definition "can contain up to ten active models"; each deployed model can carry segmentation filters, and "the first model that has filters matching a specific input row will be used to make the prediction".
- **Writeback field lifecycle.** "Removing a pushback field from the goal metadata causes the field to be deleted from the Salesforce object as well." Treat the goal file as the owner of that field.
- **UNVERIFIED (2026-10-03) claims carried from earlier versions of this skill:** story creation happens only in Analytics Studio (App Launcher, Analytics Studio, Create, Story); at most three writeback fields per object; writeback fields get no field-level security by default; refreshed models are not activated automatically; prediction definition IDs start with `1OR`. These are help-only and should be checked in the org.

---

## Questions to Ask Before Configuring

Ask these before creating a story. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which outcome are we predicting, and which fields are only known after it happens?" | Leakage fields inflate accuracy and produce useless live scores (gotcha 7) | The outcome field and an excluded-variables list | A model whose scores hold up on open records |
| "Do different segments (region, product line) behave differently enough to need their own model?" | One prediction definition holds up to ten active models; the first matching filter wins (gotcha 2) | Segment filters in priority order | Predictions from the right model for each record |
| "Which fields are sensitive, and could any act as a proxy for a protected attribute?" | Model fields carry `isSensitive` and `isDisparateImpact` flags (gotcha 6) | A reviewed list of sensitive and disparate-impact fields | A bias review on record before scores reach users |
| "Who sees the prediction field, and where?" | The writeback field lives on the record; its visibility follows field-level security (gotcha 8) | The permission sets and layouts that show the score | Scores visible to the right users from day one |
| "Will this prediction be moved between orgs with metadata?" | Removing `pushbackField` from the goal file deletes the field (gotcha 1); models are not authored in metadata (gotcha 3) | A retrieve-then-deploy procedure that never drops the field | Promotions that do not destroy the writeback field or its history |
| "Who reviews and activates each refreshed model, and how is accuracy judged?" | `terminalStateFilters` define when an outcome is final for accuracy monitoring (gotcha 5) | An owner, a cadence, and a terminal-state definition | Model drift caught by a person, not discovered by users |

What a proper setup adds over "just deploying the story": the right model scores each segment, sensitive fields are reviewed, the writeback field survives every deployment, and someone owns each refresh.

---

## Core Concepts

### Story, model, and prediction definition

| Concept | Metadata type | Key facts |
|---|---|---|
| Story | `DiscoveryStory` | The analysis Einstein Discovery builds from a dataset |
| Model | `DiscoveryAIModel` (`.model` file plus `-meta.xml`, in the `discovery` folder) | `algorithmType`, `predictionType`, `modelFields`, `status`; "write operations for DiscoveryAIModel objects are generally not supported" |
| Prediction definition | `DiscoveryGoal` (`.goal`, in the `discovery` folder) | `subscribedEntity`, `outcome`, `deployedModels`, `pushbackField`, `pushbackType`, `terminalStateFilters`, `active` |

### Algorithms and prediction types

`DiscoveryAlgorithmType` values are `Best` (tournament model), `Glm` (generalized linear model), `Gbm` (gradient boosting machine), `Xgboost`, and `Drf` (random forest). `DiscoveryPredictionType` values are `Regression`, `Classification` (binary), `MulticlassClassification`, and `Unknown`. Earlier versions of this skill said Einstein Discovery chooses only between regression and GBM; the metadata enumeration lists more algorithms. UNVERIFIED (2026-10-03): which algorithms the story wizard offers, and whether the admin chooses or the tournament picks, is help-only.

### Writeback (pushback) fields

`pushbackField` is the "automated writeback field for predictions. A custom field on the Salesforce object specified in subscribedEntity." `pushbackType` "must be set to AiRecordInsight"; `Direct` is reserved. UNVERIFIED (2026-10-03): earlier versions of this skill said the field is read-only, updates only through bulk scoring or explicit API calls (never on record save), and is limited to three per object. Test record-update behavior in a sandbox before telling users how fresh scores are.

### Model refresh and activation

Each deployed model has an `active` flag, and the prediction definition has its own `active` flag. UNVERIFIED (2026-10-03): that a completed refresh leaves the new model inactive until an admin activates it in Model Manager is help-only, but the operating rule is the same either way: someone reviews accuracy and decides which model is active.

---

## Common Patterns

### Pattern 1: End-to-end story deployment with writeback

**When to use:** Score open Opportunities with a win prediction and show the score on the record page.

**How it works:**
1. Create the story from the Opportunity dataset with the outcome and explanatory variables; exclude fields populated only after close.
2. Review model fields flagged sensitive or disparate impact before deploying.
3. Deploy the model to a prediction definition on `Opportunity`, with a writeback field and improvements if what-if suggestions are wanted.
4. Grant field-level security on the writeback field and add it to the page layout or the record page.
5. Score existing records and spot-check values.
6. Retrieve the `DiscoveryGoal` into source control so the field and model mapping are versioned (see `references/metadata-examples.md`).

### Pattern 2: Segmented prediction definition

**When to use:** Win drivers differ by region.

**How it works:** Deploy one model per region to the same prediction definition, each with a filter on the region field. Put the most specific filters first, because the first matching model scores the row. Keep a final model with no filters as the catch-all ("no filters indicates that the model matches all input rows"). Stay within ten active models.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| No CRM Analytics license | Einstein Prediction Builder | Einstein Discovery needs CRM Analytics |
| Different behavior by segment | Several deployed models with filters in one prediction definition | Up to ten active models; first matching filter wins |
| Promote to production | Retrieve `DiscoveryGoal`, deploy it, keep `pushbackField` | Removing `pushbackField` deletes the field |
| Need model authored outside Salesforce | Model Manager upload, not metadata | `UserUpload` source type is not supported in the Metadata API |
| Fresh scores at a business moment | Developer scoring API (`agentforce/einstein-discovery-development`) | Admin path is not built for event-driven scoring |
| Accuracy monitoring | Define `terminalStateFilters` | Accuracy compares predictions with outcomes that have reached a terminal state |

---

## Recommended Workflow

1. **Confirm prerequisites.** CRM Analytics license, admin permissions, target object, outcome field, and the excluded-variables list.
2. **Create and review the story.** Build it in Analytics Studio, exclude leakage fields, and review fields flagged sensitive or disparate impact.
3. **Deploy the prediction definition.** Choose segments and filters (up to ten active models), the writeback field, and improvements; define terminal-state filters for accuracy monitoring.
4. **Make the score visible.** Grant field-level security on the writeback field, add it to layouts, and score existing records.
5. **Put it under source control.** Retrieve the `DiscoveryGoal` (and the models it references) with `package.xml`; never deploy a goal file that has lost its `pushbackField`.
6. **Run refresh as an operation.** Name the owner who reviews each refreshed model's metrics and decides which model is active, then rescore.

---

## Review Checklist

- [ ] CRM Analytics license confirmed
- [ ] Leakage fields excluded from explanatory variables
- [ ] Sensitive and disparate-impact fields reviewed and recorded
- [ ] Segment filters ordered most-specific first, with a catch-all model, at most ten active models
- [ ] Writeback field field-level security and layout placement done
- [ ] `terminalStateFilters` defined for accuracy monitoring
- [ ] `DiscoveryGoal` retrieved into source control with `pushbackField` intact
- [ ] Refresh owner and activation procedure documented

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | Removing `pushbackField` from goal metadata deletes the field | A careless deploy destroys the score field |
| 2 | Up to ten active models; the first matching filter wins | Badly ordered filters send rows to the wrong model |
| 3 | `DiscoveryAIModel` write operations are generally not supported | Hand-authored model files do not deploy |
| 4 | `pushbackType` must be `AiRecordInsight` | Other values are reserved or unsupported |
| 5 | Accuracy needs a terminal-state definition | Monitoring compares against outcomes that are not final |
| 6 | Model fields carry sensitive and disparate-impact flags | Bias review skipped if nobody reads them |
| 7 | Leakage fields inflate accuracy | Live scores are poor despite great training metrics |
| 8 | Writeback visibility and refresh behavior are help-only claims | Test before promising score freshness |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Story configuration summary | Outcome, explanatory variables, excluded leakage fields, sensitive-field review |
| Prediction definition | `DiscoveryGoal` with models, segment filters, writeback field, terminal-state filters |
| Writeback field visibility | Field-level security and layout placement |
| Model refresh runbook | Owner, cadence, accuracy review, activation, rescoring |

---

## Related Skills

- `agentforce/einstein-discovery-development`: Connect REST API scoring, bulk predict jobs, and model management via API
- `agentforce/einstein-prediction-builder`: binary predictions without a CRM Analytics license
- `architect/crm-analytics-vs-tableau-decision`: whether Einstein Discovery is the right tool
- `admin/einstein-discovery-deployment`: the Flow action and Model Manager monitoring
