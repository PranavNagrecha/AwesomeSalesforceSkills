---
name: campaign-planning-and-attribution
description: "Designing Campaign Hierarchy for program-level ROI tracking, configuring Customizable Campaign Influence (CCI) attribution models, and interpreting multi-touch attribution from MCAE B2B Marketing Analytics. Trigger keywords: campaign ROI, attribution model, campaign hierarchy, first-touch, last-touch, multi-touch, CCI, campaign influence, revenue attribution, campaign member status. NOT for deciding which attribution model and KPIs to adopt before any config - use admin/marketing-reporting-requirements. NOT for MCAE connector setup or the campaign sync that writes Campaign Member records - use admin/mcae-pardot-setup. Also covers: CampaignSettings, enableCampaignInfluence2, enableAutoCampInfluenceDisabled, enableB2bmaCampaignInfluence2, enableAccountsAsCM, CampaignInfluenceModel metadata, isDefaultModel, isModelLocked, recordPreference, AllRecords, RecordsWithAttribution, CampaignInfluence.RevenueShare, ModelType, CampaignMemberStatus IsDefault HasResponded SortOrder, HierarchyActualCost, HierarchyAmountWonOpportunities, TotalNumberofResponses, Opportunity.CampaignId primary campaign source."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Scalability
triggers:
  - "How do I roll up campaign revenue from child campaigns to a parent program in Salesforce?"
  - "We need to give multiple campaigns attribution credit on the same opportunity — how do we configure that?"
  - "What is the difference between standard Campaign Influence and Customizable Campaign Influence in Salesforce?"
  - "Campaign ROI is not calculating correctly on the parent campaign — child totals are missing"
  - "How do I set up time-decay or U-shaped attribution models for Salesforce campaigns?"
  - "We want first-touch and last-touch attribution reporting on opportunities — where do we start?"
  - "Campaign member status values are not mapping to funnel stages correctly — how should these be structured?"
  - "parent campaign actual cost is blank but the child campaigns all have cost"
  - "deploy fails: CampaignSettings is not a valid package.xml metadata type name"
  - "data loader wrote the wrong campaign member status and did not error"
  - "campaign influence rows disappeared after we deactivated a model"
tags:
  - campaigns
  - campaign-hierarchy
  - attribution
  - campaign-influence
  - multi-touch-attribution
  - MCAE
  - ROI
  - B2B-marketing-analytics
  - campaign-member-status
inputs:
  - "Campaign Hierarchy design intent (program structure, depth, program vs. tactic distinction)"
  - "Attribution model requirements (first-touch, last-touch, even, time-decay, position-based)"
  - "Whether MCAE (Pardot) B2B Marketing Analytics Plus is licensed"
  - "Whether Customizable Campaign Influence is already enabled in org Setup"
  - "Existing Campaign Member Status picklist values per campaign type"
outputs:
  - "Campaign Hierarchy design recommendation with level mapping"
  - "Customizable Campaign Influence configuration plan (model type, influence rules)"
  - "Campaign Member Status structure aligned to funnel stages"
  - "Decision guidance for native CCI vs. MCAE Multi-Touch Attribution App"
  - "Completed campaign-planning-and-attribution-template.md for handoff"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Campaign Planning And Attribution

This skill activates when a practitioner needs to design Campaign Hierarchy structures for program-level ROI aggregation, configure Customizable Campaign Influence (CCI) attribution models in Salesforce, or interpret multi-touch revenue attribution data from MCAE B2B Marketing Analytics. It covers architecture decisions and configuration — not execution of individual campaigns or MCAE connector provisioning.

---

## Before Starting

Gather this context before working on anything in this domain:

| Check | What the platform actually says |
|---|---|
| Is Customizable Campaign Influence on? | `CampaignSettings.enableCampaignInfluence2` — "Indicates whether Customizable Campaign Influence is enabled… **The default value is true.**" Do not assume it needs turning on; retrieve `settings/Campaign.settings-meta.xml` and read it |
| Is Campaign Influence 1.0 still in play? | It cannot be, if CCI is on: "When true, Campaign Influence 1.0 is hidden from users and is no longer active", and `enableAutoCampInfluenceDisabled` states "`enableCampaignInfluence2` must be **false** to use this setting" |
| Can the user even see Campaigns? | `Campaign` and `CampaignMemberStatus` are "defined only for those organizations that have the marketing feature enabled and valid marketing licenses… accessible only to those users that are enabled as marketing users" — otherwise they are absent from `describeGlobal()` entirely |
| Which fields carry hierarchy totals? | Not `ActualCost` / `AmountWonOpportunities`. Those are single-campaign fields. The hierarchy totals are `HierarchyActualCost`, `HierarchyAmountWonOpportunities`, `TotalNumberofResponses` and their siblings |
| How deep can the hierarchy go? | UNVERIFIED (2026-09-05): no maximum Campaign hierarchy depth appears in the Object Reference, the Metadata API guide, or the App Limits cheat sheet (`grep -i campaign` over the cheat sheet returns zero hits). The commonly-quoted "5 levels" has no source here — confirm in the org, do not design to a number you cannot cite |
| Does an external system publish models? | `enableB2bmaCampaignInfluence2` — "whether your org can access campaign influence models from other systems, such as Pardot"; requires `enableCampaignInfluence2` = true |

Sources for the quotes above: `api_meta.txt:111556–111571`, `object_reference.txt:57860–57863`, `object_reference.txt:57273–57359`, `object_reference.txt:57708–57802`, `object_reference.txt:58672–58675`. Full line-by-line grounding is in `references/worked-examples.md`.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which single question does the attribution number have to answer — who to pay, where to spend next, or what to report to the board?" | Only one model can be the default, and only the default model's records appear on campaigns and opportunities. Everything else is report-only | The name of the default model, and an explicit statement that the others are reporting artefacts |
| "Are campaigns run per region, per product line and per quarter at the same time?" | Each dimension someone wants to slice by is either a hierarchy level or a Campaign field, and hierarchy headroom is the resource you cannot cite a limit for | The dimension list, split into "hierarchy" and "custom field on Campaign" |
| "Who writes Campaign Member records — a person, a data load, or Account Engagement?" | An invalid `Status` is silently coerced to the campaign's default status, not rejected. A loader is the one writer that will never notice | The writer list, and whether each writer sends the status *text* (required) or an Id (silently wrong) |
| "For each campaign type, which status means 'they responded' to the business?" | `HasResponded` on the status is what `NumberOfResponses` and `HierarchyNumberOfResponses` count. Since API 39.0 at least one status per campaign must have it | The per-type status table with exactly one default and at least one responded flag |
| "Will anything other than the recalculation job write CampaignInfluence rows?" | A locked model can only be written via the API; rows written against the Primary Campaign Source model are deleted on recalculation | The writer for each model, and a decision on `isModelLocked` per model |
| "Is anyone allowed to deactivate a model once the quarter's reporting is out?" | Deactivating a model **deletes** its campaign influence records. There is no undo, and reactivating does not restore them | A named owner for model lifecycle and a change-control note in the release calendar |
| "Which reports and dashboards will read this, and who runs them?" | Campaign visibility is licence- and marketing-user-gated before sharing is even considered; a report that returns nothing is often an access problem | The consuming report list with the running user's licence and marketing-user flag confirmed |

What a proper configuration adds over just enabling Campaign Influence: the default model is a deliberate choice rather than whatever shipped, member statuses cannot silently coerce a load into the wrong funnel stage, hierarchy totals are read from the fields that actually hold them, and deactivating a model is a governed change rather than an irreversible data deletion someone discovers a quarter later.

---

## Core Concepts

### Campaign Hierarchy and where the totals actually live

Campaigns nest through `ParentId`, a lookup to `Campaign` (`ParentCampaign` is the read-only label for "the campaign above the selected campaign in the campaign hierarchy"). The rollup is not a Master-Detail roll-up summary you configure — it is a set of pre-built **calculated** fields with distinct names.

| Scope | Field |
|---|---|
| This campaign only | `ActualCost`, `BudgetedCost`, `ExpectedRevenue`, `NumberOfLeads`, `NumberOfResponses`, `AmountAllOpportunities`, `AmountWonOpportunities` |
| The whole hierarchy | `HierarchyActualCost`, `HierarchyBudgetedCost`, `HierarchyExpectedRevenue`, `HierarchyNumberOfLeads`, `HierarchyNumberOfResponses`, `HierarchyAmountAllOpportunities`, `HierarchyAmountWonOpportunities` |
| The whole hierarchy, second family | `TotalAmountAllOpportunities`, `TotalAmountAllWonOpportunities`, `TotalNumberofLeads`, `TotalNumberofOpportunities`, `TotalNumberofResponses`, `TotalNumberofWonOpportunities` |

`HierarchyNumberOfResponses` counts "contacts and unconverted leads with a Member Status equivalent to 'Responded' for the campaign in a campaign hierarchy" (`object_reference.txt:57353–57359`). Two independently named families cover the same idea; pick one per report and say which in the report description, because a dashboard mixing `Hierarchy*` and `Total*` columns will look inconsistent for reasons no one can see.

### Customizable Campaign Influence

`CampaignInfluence` is "the association between a campaign and an opportunity in Customizable Campaign Influence", available in API 37.0 and later, and the Object Reference is explicit that it "applies only to Customizable Campaign Influence and not to Campaign Influence 1.0". Its fields are `CampaignId`, `CampaignMemberId`, `ContactId`, `Influence` (percent), `ModelId`, `OpportunityContactRoleId`, `OpportunityId` and **`RevenueShare`** — there is no field called `Revenue`.

`CampaignInfluenceModel` is read-only as an sObject (`describeSObjects()`, `query()`, `retrieve()` only) but is addable as a metadata component. Its `ModelType` picklist is a closed set:

| Value | Model |
|---|---|
| 1 | Primary Campaign Source Model |
| 2 | Custom Model |
| 3 | First Touch Model |
| 4 | Last Touch Model |
| 5 | Even Distribution Model |
| 6 | Data-Driven Model |

The metadata type carries no `modelType` element, so a model you deploy arrives as a custom model. What you *do* control on deploy is `isActive`, `isDefaultModel`, `isModelLocked`, `modelDescription`, `name` and `recordPreference`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CampaignInfluenceModel xmlns="http://soap.sforce.com/2006/04/metadata">
    <isActive>true</isActive>
    <isDefaultModel>false</isDefaultModel>
    <isModelLocked>true</isModelLocked>
    <modelDescription>100% influence attribution to the last campaign that touched the contact.</modelDescription>
    <name>Acme Last Touch</name>
    <recordPreference>RecordsWithAttribution</recordPreference>
</CampaignInfluenceModel>
```

`recordPreference` is the switch most designs get wrong: `AllRecords` "creates records regardless of the revenue attribution percentage"; `RecordsWithAttribution` "creates records only when the revenue attribution is greater than 0%". Choosing `AllRecords` on a high-volume org multiplies row count by every touched campaign, including the ones credited nothing.

**UNVERIFIED (2026-09-05):** the claim that CCI requires Opportunity Contact Roles is not stated in any of the eight official extracts. What *is* documented is that `CampaignInfluence` carries `ContactId` and `OpportunityContactRoleId` fields (`object_reference.txt:57941–57946, 57963–57969`), which makes contact-role population a strong practical prerequisite but not a quoted platform rule. Verify in the org before presenting it as a requirement.

### Campaign Member Status and funnel tracking

Two objects share the name. The org-wide default list is a `StandardValueSet` whose `fullName` is `CampaignMemberStatus`, mapping to `CampaignMember.Status` (`api_meta.txt:141856`). The per-campaign list is the `CampaignMemberStatus` **sObject** — `CampaignId`, `Label` (765 characters), `IsDefault`, `HasResponded`, `SortOrder` — and it is not a metadata type at all.

`CampaignMember.HasResponded` is read-only; `Status` controls it. Since API version 39.0, every campaign must have a default status and at least one status with `HasResponded` = true. A status that is the default, or is in use on a campaign, cannot be deleted.

### MCAE Multi-Touch Attribution App

**UNVERIFIED (2026-09-05):** time-decay, position-based / U-shaped models, the "Multi-Touch Attribution App", and any weighting percentages for them appear nowhere in the Metadata API guide, the Object Reference, or the other six extracts (`grep -i "time.decay\|u-shaped\|position-based\|multi-touch"` returns no hits). The only related grounded facts are `CampaignSettings.enableB2bmaCampaignInfluence2` ("whether your org can access campaign influence models from other systems, such as Pardot") and `PardotSettings.enableEnhancedProspectCustomFieldsSync` ("Enable Object Sync to enhance with B2B Marketing Analytics or B2B Marketing Analytics Plus"). Treat model names and weightings from Account Engagement as vendor documentation to confirm in the org, and never present a 40/40/20 split as a platform fact. `admin/mcae-pardot-setup` owns the connector itself.

---

## Common Patterns

### Pattern: Program/Tactic Hierarchy with Rolled-Up ROI Dashboard

**When to use:** A marketing team runs multiple channels (email, webinar, paid) under a single program and needs a unified ROI view at the program level for executive reporting.

**How it works:**
1. Create a parent Campaign at the program level. Set `BudgetedCost` and `ExpectedRevenue` here.
2. Create child Campaigns (Type = Email, Webinar, Advertisement) and link them via `ParentId`.
3. Populate `ActualCost` on each **child** campaign as spend is confirmed.
4. Build the program dashboard on `HierarchyActualCost` and `HierarchyAmountWonOpportunities` on the parent — not on `ActualCost`, which only ever holds the parent's own spend.
5. State the field family used in the report description so a second author does not mix `Hierarchy*` with `Total*`.

**Why not the alternative:** Without hierarchy, teams manually aggregate per-channel costs into a spreadsheet. This breaks when campaigns are added mid-program and creates reconciliation debt.

### Pattern: Dual-model CCI — one default, one reporting-only

**When to use:** Revenue operations needs first-touch and last-touch views side by side.

**How it works:**
1. Retrieve `settings/Campaign.settings-meta.xml` and confirm `enableCampaignInfluence2` is true.
2. Deploy two `CampaignInfluenceModel` files. Exactly one carries `isDefaultModel` = true; that one drives the Campaign Influence related list on opportunities, the Influenced Opportunities related list on campaigns, and the Campaign Statistics section.
3. Set `isModelLocked` = true on both so only the API writes rows, then name the writer for each.
4. Set `recordPreference` = `RecordsWithAttribution` unless zero-credit rows are genuinely wanted.
5. Build one custom report type on `CampaignInfluence` joined to `Opportunity` and group by `ModelId` — one report type serves both models.

**Why not the alternative:** Two report types, one per model, doubles the maintenance for no gain: `ModelId` is a column, not a schema difference.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need program-level ROI across multiple campaign tactics | Campaign Hierarchy, dashboard on `Hierarchy*` fields | The `Hierarchy*` and `Total*` families are the only fields that aggregate descendants |
| Need multiple campaigns to share credit on one opportunity | CCI with one custom model per view | Only CCI produces multiple `CampaignInfluence` rows per opportunity per model |
| Need time-decay or U-shaped models | Confirm the capability in the org first, then MCAE / B2BMA Plus | UNVERIFIED (2026-09-05): those model names are absent from the official extracts; `ModelType` documents six values and none of them is time-decay |
| Someone asks to "turn off Campaign Influence 1.0 first" | Check `enableCampaignInfluence2` — if true, 1.0 is already hidden and inactive | `enableAutoCampInfluenceDisabled` is only usable while `enableCampaignInfluence2` is false |
| A model's rows are wrong and someone wants to "reset" it | Never by deactivating | Deactivating a model deletes its campaign influence records |
| Attribution rows exist but the related lists are empty | Check which model is default | Only the default model's records appear on campaigns and opportunities |
| Need real-time campaign spend reporting | Report on child Campaign `ActualCost` directly | The `Hierarchy*` fields are documented as calculated; no refresh SLA is published |

---

## Recommended Workflow

1. **Retrieve before designing** — `sf project retrieve start --metadata CampaignInfluenceModel --metadata "Settings:Campaign" --metadata "CustomObject:Campaign"`. Read `enableCampaignInfluence2`, `enableB2bmaCampaignInfluence2` and `enableAccountsAsCM` off the retrieved file rather than asking. Confirm the running user is a marketing user with a marketing licence, or `Campaign` will not describe at all.
2. **Answer the seven questions above and fill `templates/campaign-planning-and-attribution-template.md`** — in particular the default-model choice, the per-type status table, and the model-lifecycle owner.
3. **Write the campaign plan record** — the YAML artefact in `references/worked-examples.md` § 1: hierarchy, naming regex, member status sets, attribution models. This is the single source the rest of the build is generated from.
4. **Lint it** — `python3 scripts/check_campaign_planning_and_attribution.py --file <plan>.yaml --manifest-dir force-app/main/default`. It fails on a duplicate campaign id, a name that breaks the naming regex, a status set without exactly one default or without a responded status, a `model_type` outside the six documented values, more than one `is_default_model`, a bad `recordPreference` enum, and a record type whose `Type` picklist values are not in the plan.
5. **Generate and deploy the metadata** — `CampaignSettings`, the `CampaignInfluenceModel` files, Campaign fields and record type, the two standard value sets, and the report type, using the package.xml in `references/worked-examples.md` § 7 (remember: settings are declared under `<name>Settings</name>`, and `RecordType` and `StandardValueSet` do not accept `*`).
6. **Create the per-campaign member statuses** — these are sObject rows, not metadata. Run the member-status health query in § 9 afterwards to catch any campaign left without exactly one default.
7. **Run the acceptance tests in § 10** — especially A4 (deactivation deletes rows), A5 (invalid status coerces to default), and A7 (Lead + Contact on one member inserts silently as Contact only). Record the results in the template before handing over.

---

## Review Checklist

- [ ] `enableCampaignInfluence2` read from the retrieved settings file, not assumed
- [ ] Exactly one `CampaignInfluenceModel` has `isDefaultModel` = true
- [ ] `recordPreference` is a deliberate choice per model, not a copied default
- [ ] `isModelLocked` matches the named writer for each model
- [ ] Dashboards read `Hierarchy*` / `Total*` fields, never `ActualCost` as a rollup
- [ ] One field family (`Hierarchy*` or `Total*`) per report, stated in the description
- [ ] Every campaign has exactly one default member status and at least one responded status
- [ ] Every writer of `CampaignMember` sends the status **text**, never the status Id
- [ ] Model deactivation has a named owner and a change-control entry
- [ ] Report consumers are marketing users with a marketing licence
- [ ] `scripts/check_campaign_planning_and_attribution.py` exits 0 on the plan and the manifest

---

## Salesforce-Specific Gotchas

The nine behaviours behind most campaign-attribution incidents are in `references/gotchas.md`, each with what happens, when it occurs, how to avoid it, and its guide line range. The three that cost the most:

| # | Behaviour |
|---|---|
| 1 | Deactivating an influence model **deletes** its rows; reactivating does not bring them back |
| 2 | An invalid `CampaignMember.Status` is coerced to the campaign's default status and inserts cleanly — nothing errors |
| 3 | `ActualCost` on a parent campaign is that campaign's own spend; the hierarchy total is `HierarchyActualCost` |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Campaign plan record (YAML) | Hierarchy, naming convention, per-type member status sets, attribution models — the input to the checker |
| `Campaign.settings-meta.xml` | The org switches, retrieved and re-deployed deliberately |
| `*.campaignInfluenceModel-meta.xml` | One file per model, with the default and lock decisions recorded |
| Campaign fields + record type | The dimensions kept off the hierarchy |
| `*.reportType-meta.xml` | `CampaignInfluence` joined to `Opportunity`, grouped by model |
| Acceptance test results | The ten Given/When/Then rows, run in the UAT sandbox |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Building anything — the Acme quarter carried end to end: the plan YAML, `CampaignSettings`, three `CampaignInfluenceModel` files, Campaign fields and record type, both standard value sets, the report type, package.xml with its four wildcard answers, the retrieve/deploy commands, the ROI and attribution SOQL, and ten acceptance tests |
| `references/gotchas.md` | Nine platform behaviours behind most attribution incidents — model deactivation deleting rows, status coercion, the two rollup field families, Lead-XOR-Contact, Primary Campaign Source rows being recalculated away |
| `references/examples.md` | Three worked designs — hierarchy ROI, dual-model CCI, and the member-status repair — plus the anti-pattern of automating on a calculated campaign field |
| `references/well-architected.md` | Pillar mapping, the architectural tradeoffs, and the official-source list behind every claim in this package |
| `references/llm-anti-patterns.md` | Self-checking generated output — the ways an assistant gets campaign attribution wrong |
| `templates/campaign-planning-and-attribution-template.md` | Capturing the design before building it: hierarchy table, status sets, model decisions, and the manual-Setup register |

---

## Related Skills

- `admin/mcae-pardot-setup` — MCAE connector provisioning, business units, and the campaign sync that feeds attribution data into Salesforce
- `admin/marketing-reporting-requirements` — agreeing which attribution model and which KPIs before any configuration exists
- `admin/opportunity-management` — `Opportunity.CampaignId` (the primary campaign source), contact roles, stages and splits
- `admin/lead-management-and-conversion` — what conversion does to campaign membership and lead-sourced attribution
- `admin/report-type-strategy` — choosing the base object and join shape for the influence report type
- `admin/reports-and-dashboards` — building the report and dashboard on top, folder sharing, and the running user
