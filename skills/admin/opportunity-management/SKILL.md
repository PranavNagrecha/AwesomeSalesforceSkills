---
name: opportunity-management
description: "Configuring Salesforce opportunity management: sales stages, sales processes, opportunity record types, Path configuration, opportunity teams, opportunity splits, and forecasting categories. Use when setting up or restructuring the opportunity lifecycle for Sales Cloud. NOT for forecast types, rollup methods, quotas or manager adjustments — use admin/collaborative-forecasts. NOT for agreeing what the stages and exit criteria should be before any build — use admin/sales-process-mapping. NOT for CPQ pricing or product configuration. Keywords: BusinessProcess, sales process, OpportunityStage, ForecastCategoryName, PathAssistant, OpportunitySplit, OpportunitySplitType, OpportunityTeamMember, Opportunity.settings, enableOpportunityTeam, IsClosed, IsWon, IsPrivate."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "stage is missing from the opportunity picklist for one record type"
  - "opportunities are not showing up in the forecast for a new stage"
  - "deploy fails with INVALID_CROSS_REFERENCE_KEY on an Opportunity business process"
  - "set up separate sales processes for new business and renewals"
  - "split opportunity revenue between two reps and have both forecasts roll up"
  - "reps are skipping stages and Path is not stopping them"
  - "cannot turn off opportunity splits after enabling them"
  - "add Path guidance and key fields to Opportunity stages"
  - "opportunity team members cannot see the deal they were added to"
  - "probability keeps resetting when the stage changes"
  - "opportunity stage probability overwritten when the stage changes"
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
  - business-process
  - opportunity-teams
inputs:
  - "List of sales stages needed per business motion (e.g., new logo vs. renewal)"
  - "Whether splits are required and which type (revenue vs. overlay)"
  - "Forecast types needed and whether Collaborative Forecasting is enabled"
  - "Existing record types and which sales process should apply to each"
outputs:
  - "Ordered configuration checklist for stages, sales processes, record types, and Path"
  - "Deployable BusinessProcess, RecordType, PathAssistant and Opportunity.settings XML"
  - "Decision guidance on whether to use revenue vs. overlay splits"
  - "Validation rules approach for enforcing stage progression"
  - "Forecast category mapping for each stage"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Opportunity Management

This skill activates when configuring or restructuring the opportunity lifecycle in Sales Cloud: defining stages, building sales processes, assigning them to record types, adding Path guidance, enabling team selling and splits, and aligning stages to forecast categories. The configuration chain has a strict dependency order — skipping or reversing steps causes broken picklists, forecast gaps, or data integrity issues.

---

## Before Starting

Gather this context before working on anything in this domain:

- Know whether the org uses Collaborative Forecasting and which forecast object it uses (Opportunity, Opportunity Product, Opportunity Split, or Product Schedule) — this determines how splits feed forecasts.
- Confirm whether Opportunity Splits has ever been enabled. Splits cannot be disabled once any split data exists, and the setup order relative to Team Selling is non-negotiable.
- Identify how many distinct sales motions exist (e.g., direct new logo, renewal, channel partner) — each may need its own Sales Process, which means its own record type and stage subset.
- Check how many custom forecast types the org already has, and confirm the ceiling with the org's own limits page before promising a new one. <!-- UNVERIFIED (2026-09-04): the "4 by default, 7 with Support" figure is carried over from the previous revision of this skill; no custom-forecast-type limit appears in api_meta.txt, object_reference.txt, or salesforce_app_limits_cheatsheet.txt. -->

---

## Questions to Ask Before Configuring

Ask these before touching Setup. Each one maps to a gotcha in `references/gotchas.md`, and an LLM that skips them produces a stage ladder that deploys green and forecasts wrong.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which forecast bucket does each stage belong in, and who signed off on that mapping?" | `ForecastCategoryName` is per-stage and the forecast rolls up by category, not by stage; two stages in the same bucket collapse the distinction the ladder was built to create | The stage → category table, which is the input to the `StandardValueSet` deploy |
| "Which stages does each motion actually use, and which motion is the default?" | A `BusinessProcess` is a subset of the global value set, and a record type binds exactly one; the subset decision drives how many record types you need | The process-to-record-type matrix, and the count of record types the change really costs |
| "Does any integration or Apex write `Probability` or `ForecastCategoryName` directly?" | Both are overridable per record, and a `StageName` update in the same transaction silently overwrites the override (Gotcha 9) | The list of writers to fix before the ladder ships, not after |
| "Are splits genuinely permanent for this business, and does anyone need overlay credit?" | Splits are a one-way door, split types cannot be created or deleted through any API, and `IsTotalValidated` is fixed at creation (Gotcha 11) | A signed decision plus the exact split types someone must hand-build in every org |
| "Do team members need Read, Edit, or All on the deals they join?" | `OpportunityTeamMember.OpportunityAccessLevel` is the access grant; adding someone to a team is a sharing change, not a UI change | The access level per team role, checked against OWD |
| "Will any opportunity ever be marked Private?" | `IsPrivate` removes teams, splits **and** sharing from the record (Gotcha 10) — it silently defeats the whole team-selling design | An explicit rule for who may set Private, or a decision to hide the field |
| "How will we measure stage movement six months from now?" | History cannot be backfilled, and `OpportunityHistory` is not a stage-history table (Gotcha 12) | Field history tracking switched on now, and the right query chosen up front |

What a proper configuration adds over just building the stages: the forecast agrees with the pipeline report, each motion sees only its own stages, splits and teams grant the access they were meant to grant, and stage movement is measurable from the day the ladder ships.

---

## Core Concepts

### Stage Values and Their Platform-Level Properties

`Opportunity.StageName` is backed by the standard value set named `OpportunityStage`. The stage row itself is queryable as the `OpportunityStage` object, which supports only `describeSObjects()`, `query()` and `retrieve()` (object_reference.txt:195438–195439) — you read it to verify, and change it through `StandardValueSet` metadata, which `admin/picklist-and-value-sets` owns.

Each stage carries `IsActive`, `IsClosed`, `IsWon`, `DefaultProbability`, `ForecastCategoryName` and `SortOrder`. Those defaults propagate to the record: "If the `StageName` is updated, then the `ForecastCategoryName`, `IsClosed`, `IsWon`, and `Probability` are automatically updated based on the stage-category mapping" (object_reference.txt:192903–192905).

Three of those behave differently on the record than admins expect:

| Record field | Behaviour | Source |
|---|---|---|
| `IsClosed`, `IsWon` | "Directly controlled by `StageName`. You can query and filter on this field, but you can't directly set it" | object_reference.txt:192558, 192633 |
| `Probability`, `ForecastCategoryName` | "implied, but not directly controlled, by the `StageName` field. You **can** override this field to a different value" | object_reference.txt:192487–192489 |
| `ExpectedRevenue` | "Read-only field that is equal to the product of the opportunity `Amount` field and the `Probability`" | object_reference.txt:192406–192408 |

### Forecast Categories Have Two Vocabularies

This is the correction most stage ladders need. The value you write in metadata is **not** the value you read in SOQL:

| Where | Field | Allowed values | Source |
|---|---|---|---|
| Metadata XML | `forecastCategory` on a `StandardValue` / `CustomValue` | `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed` | api_meta.txt:47578–47586 |
| SOQL / UI | `OpportunityStage.ForecastCategoryName`, `Opportunity.ForecastCategoryName` | `Best Case`, `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline` | object_reference.txt:195499–195505, 192491–192497 |
| SOQL (derived) | `Opportunity.ForecastCategory` | `BestCase`, `Closed`, `Forecast`, `MostLikely`, `Omitted`, `Pipeline` | object_reference.txt:192474–192481 |

Metadata `Forecast` is what the UI calls **Commit**. Neither `Commit` nor `MostLikely` is a member of the `ForecastCategories` enumeration that the `forecastCategory` element accepts, so a stage table transcribed from a SOQL export cannot be written into a `standardValueSet` file as read. See `references/gotchas.md` Gotcha 13.

### Sales Processes and the Configuration Chain

A Sales Process is a `BusinessProcess` — a filtered view of the global stage value set. The guide: it "enables you to display different picklist values for users based on their profile. Multiple business processes allow you to track separate sales, support, and lead lifecycles" (api_meta.txt:42956–42958). The dependency chain must be followed in this exact order:

1. Define all stage values in the `OpportunityStage` standard value set, with `forecastCategory`, `probability`, `won` and `closed` set.
2. Create a `BusinessProcess` per business motion, listing only the stages relevant to that motion.
3. Bind each Opportunity `RecordType` to exactly one `businessProcess`.
4. Configure a `PathAssistant` on top of that record type's stages.

A stage not listed in a Sales Process cannot appear on any record type built from that process, and cannot be a Path step. Path adds guidance and key fields per stage; it does not enforce progression — enforcement is validation rules.

One warning the guide states outright and most designs miss: "**Don't use business processes as an access control mechanism.** Profile assignment governs create and edit access for business process but doesn't govern read access… Don't store sensitive information in the business process description, name, or picklist values" (api_meta.txt:42960–42965).

### Path Configuration

`PathAssistant` is deployable metadata with three fields that are **not updateable**: `entityName`, `fieldName` and `recordTypeName` (api_meta.txt:94513–94530). Retargeting a Path at a different record type is a delete-and-recreate.

The hard structural rule: "Only one path can be created per record type for each object, including `__Master__` record type" (api_meta.txt:94496). Two motions that need different guidance need two record types — Path cannot branch inside one.

Two more that surprise people: a stage with no `pathAssistantSteps` block still renders as a chevron, because "a missing step in the .xml file means it has not been configured, not that it doesn't exist" (api_meta.txt:94524–94526); and "the preference does not need to be on to retrieve or deploy PathAssistant" (api_meta.txt:94498), so a green Path deploy proves neither that Path is enabled nor that the component is on the Lightning page.

### Team Selling and Opportunity Splits

Team selling is switched on with `enableOpportunityTeam` in `Opportunity.settings` — "Lets users associate team members with opportunities" (api_meta.txt:123333). It is the only part of the team/splits chain that is deployable.

Splits are not. There is no `OpportunitySplitType` metadata type, and the `OpportunitySplitType` object supports only `describeSObjects()`, `query()`, `retrieve()` and `update()` — **no `create()`, no `delete()`** (object_reference.txt:195284–195285). Split types are hand-built in Setup in every org, and `IsTotalValidated` ("If true, the split must total 100%. If false, the split can total any percentage", object_reference.txt:195329–195334) is `Create, Defaulted on create, Filter, Group, Sort` with no `Update` — the validation behaviour is fixed the moment the type is created.

The percentage ceiling follows from that flag: `SplitPercentage` "If the split type is validated to a 100% total, this number can range from 0 to 100. If the total isn't validated, this number can range from 0 to 1,000" (object_reference.txt:195208–195212).

Adding a user to a team is a sharing change. `OpportunityTeamMember.OpportunityAccessLevel` takes `Read`, `Edit` or `All` (object_reference.txt:195697–195700). Splits cannot be disabled after split data has been saved — treat it as a one-way door.

---

## Common Patterns

### Multi-Motion Sales Process Setup

**When to use:** The org serves different buyer motions (e.g., new logo, renewal, channel partner) that move through different stage sequences.

**How it works:**
1. Define all stage values in the `OpportunityStage` standard value set. Set `forecastCategory`, `probability`, `won` and `closed` on every stage — see `admin/picklist-and-value-sets` §3.
2. Create one `BusinessProcess` per motion (`New Business`, `Renewal`), listing only that motion's stages. Nested `<businessProcesses><fullName>` takes the **bare** name; `package.xml` takes `Opportunity.New Business` (api_meta.txt:42993–43008).
3. Bind each `RecordType` to one `businessProcess`.
4. Build one `PathAssistant` per record type — one path per record type is the platform ceiling.
5. Write validation rules that reference `RecordType.DeveloperName` to enforce stage-specific field requirements per motion.

**Why not a single process:** A single catch-all process forces reps through irrelevant stages and pollutes forecast data with stages that don't match the motion's pipeline semantics.

### Revenue Split + Forecast Type Alignment

**When to use:** Multiple reps share credit on deals and the business needs their individual quotas reflected in forecasting.

**How it works:**
1. Deploy `enableOpportunityTeam` as `true` in `Opportunity.settings`.
2. Enable Opportunity Splits in Setup, then hand-build the split types there — no API creates them.
3. Point a `ForecastingType` at the split type by name via `opportunitySplitType` (api_meta.txt:75253–75254); the guide's own samples use `Revenue` and `Custom_Revenue` (api_meta.txt:75316, 75330).
4. Create a separate forecast type for overlay credit if overlay tracking is needed.
5. Assign forecast types to users. Everything past step 3 belongs to `admin/collaborative-forecasts`.

**Why not use Opportunity Amount:** Amount-based forecasting double-counts when multiple reps appear in splits. Split-based forecasting credits each rep's share.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Two business motions with different stages | Separate `BusinessProcess` + `RecordType` per motion | Prevents stage contamination across motions; keeps forecast rollups clean |
| Two motions need different Path guidance on the same stages | Still two record types | Only one Path per record type per object (api_meta.txt:94496) |
| Need to guide reps on key fields per stage | Configure `PathAssistant` | Path provides inline guidance without requiring custom layouts per stage |
| Need to prevent reps from skipping required stages | Add validation rules (not Path) | Path is visual only — it does not block saves |
| Multiple reps need credit on a deal | Split type with `IsTotalValidated = true` | Splits feed forecast rollups per rep; Amount-only forecasting double-counts |
| Overlay team (SEs, pre-sales) need separate credit | A second, non-validated split type + its own forecast type | Non-validated splits accept 0–1,000% (object_reference.txt:195208–195212) without touching quota |
| Split types need to move between orgs | They don't — build them in Setup per org | `OpportunitySplitType` has no `create()` and no metadata type |
| Stage retired for one motion only | Remove it from that `BusinessProcess`; leave the value active | Records keep the value; only the picklist changes for that record type |
| Stage retired org-wide | Reassign records, then deactivate — never delete while records use it | Inactive values "are not available in the picklist and are retained for historical purposes only" (object_reference.txt:195512–195514) |
| Business wants its own forecast category names | Not possible — pick from the fixed enums | Both `ForecastCategory` and `ForecastCategoryName` are restricted picklists with fixed value lists |

---

## Recommended Workflow

1. **Read the neighbours before writing any XML.** `admin/picklist-and-value-sets` §3 owns the `OpportunityStage` standard value set; `admin/record-types-and-page-layouts` owns the `RecordType`/`businessProcess` pairing; `admin/collaborative-forecasts` owns everything past `ForecastingType`. Design questions about which stages should exist at all are `admin/sales-process-mapping` and the `/design-sales-stages` agent.
2. **Retrieve the current shape**, using the `sf project retrieve start` block in `references/metadata-examples.md` §7. Never author a `standardValueSet` for stages from scratch — a partial file deactivates every value it omits.
3. **Fix the stage ladder first.** Confirm every stage has `forecastCategory`, `probability`, `won` and `closed`, using the metadata vocabulary (`Forecast`, not `Commit`) from `## Core Concepts`. Verify with query 8a in `references/metadata-examples.md` §8.
4. **Write the `BusinessProcess` per motion, then bind the record types**, following §2 of `references/metadata-examples.md`. Watch the two `fullName` forms — bare inside `<CustomObject>`, object-qualified in `package.xml`.
5. **Add the `PathAssistant`** per §3, one per record type, with every `picklistValueName` drawn from that record type's business process. Note separately which of those steps need validation-rule enforcement; Path enforces nothing.
6. **Decide splits and teams explicitly.** Deploy `enableOpportunityTeam` (§1); record the split types someone must build by hand in each org (§6); set the per-role `OpportunityAccessLevel`.
7. **Run the checker and the verification queries.** `python3 skills/admin/opportunity-management/scripts/check_opportunity_management.py --manifest-dir force-app/main/default`, then queries 8a–8d and the Setup-only check 8e in `references/metadata-examples.md` §8. Clear every ERROR before deploying; triage WARN and INFO.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every stage value carries `forecastCategory`, `probability`, `won` and `closed`, using the **metadata** vocabulary (`Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed`)
- [ ] Every stage with `won = true` also has `closed = true`; `Closed Lost` maps to `Omitted`, not `Closed`
- [ ] Each `BusinessProcess` contains at least one won and one lost stage, and only stages valid for that motion
- [ ] No two business processes on Opportunity share a `fullName`
- [ ] Each active Opportunity `RecordType` carries a `businessProcess` (bare name, not object-qualified)
- [ ] Each `PathAssistant` has `recordTypeName` pointing at a record type in the same deploy, and every `picklistValueName` exists in that record type's business process
- [ ] No record type has two Paths; no Path was "edited" to change `entityName`, `fieldName` or `recordTypeName`
- [ ] `enableOpportunityTeam` is `true` in `Opportunity.settings` before splits are switched on in Setup
- [ ] Split types are documented as a manual Setup step per org, with `IsTotalValidated` chosen deliberately — it cannot be changed later
- [ ] Query 8d returns zero rows (every validated split totals 100)
- [ ] No stage value with active records was deleted; deactivation was used instead
- [ ] Validation rules enforcing stage progression exist and are tested; Path alone is not treated as enforcement
- [ ] Anyone who can set `IsPrivate` understands it removes teams, splits and sharing from the record

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The metadata forecast-category vocabulary is not the SOQL one** — metadata takes `Forecast`; SOQL and the UI say `Commit`. `MostLikely` is readable but has no metadata token at all.
2. **Setting `StageName` in the same update as a `Probability` override loses the override** — the platform recomputes `Probability`, `ForecastCategoryName`, `IsClosed` and `IsWon` from the stage on every stage change.
3. **`IsPrivate` deletes the team-selling design on that record** — teams, splits and sharing are all removed when the flag is set.
4. **Split types have no `create()` and no metadata type** — every org needs them hand-built, and `IsTotalValidated` is frozen at creation.
5. **Path enforces nothing** — it is a visual guidance layer; reps can save at any stage regardless of Path configuration. Stage progression enforcement requires validation rules.

Deeper treatment, with sources, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `settings/Opportunity.settings-meta.xml` | Team selling, field history tracking and similar-opportunity filters, deployable as `Settings:Opportunity` |
| `businessProcesses/*.businessProcess-meta.xml` | One sales process per motion, each a subset of the stage value set |
| `recordTypes/*.recordType-meta.xml` | Record types bound to their business process |
| `pathAssistants/*.pathAssistant-meta.xml` | One Path per record type, with key fields and guidance per stage |
| Stage audit table | Output of query 8a: every stage with `IsActive`, `IsClosed`, `IsWon`, `DefaultProbability`, `ForecastCategoryName`, `SortOrder` |
| Manual-Setup register | Splits enablement, split types, and Lightning page placement — the states no deploy can carry |
| Checker output | `check_opportunity_management.py` findings, ERROR / WARN / INFO |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable `OpportunitySettings`, `BusinessProcess`, `RecordType`, `PathAssistant` and `Layout` XML, the package.xml with its four different wildcard answers, and the verification SOQL |
| `references/gotchas.md` | Sixteen platform behaviours behind most opportunity-lifecycle incidents — the two forecast vocabularies, stage-change overwrite, `IsPrivate`, split-type immutability, and what `OpportunityHistory` actually records |
| `references/examples.md` | Worked two-process, revenue-split and stage-enforcement designs, with the validation-rule formulas and the pre-deletion audit query |
| `references/well-architected.md` | Pillar mapping, the architectural tradeoffs, and the official-source list behind every claim in this package |
| `references/llm-anti-patterns.md` | Self-checking generated output — the ways an assistant gets the opportunity lifecycle wrong |
| `templates/opportunity-management-template.md` | Capturing the design before building it: motions, stage-to-category table, splits decision, and the manual-Setup register |

---

## Related Skills

- admin/sales-process-mapping — agree the stages and their exit criteria before any of this is built
- admin/picklist-and-value-sets — owns the `OpportunityStage` standard value set and its partial-deploy trap
- admin/record-types-and-page-layouts — owns the `RecordType` / `businessProcess` pairing and layout assignment
- admin/path-and-guidance — deep Path configuration: supported field types, guidance content, celebration triggers
- admin/collaborative-forecasts — forecast types, rollups, quotas and adjustments once the categories are mapped
- admin/enterprise-territory-management — territory-based opportunity assignment and territory forecast rollups
- admin/record-type-strategy-at-scale — how many record types the org should carry before this design adds more
