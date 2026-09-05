# Campaign Planning And Attribution — Work Template

Use this template when designing Campaign Hierarchy structures, configuring Customizable Campaign Influence (CCI), or planning multi-touch attribution reporting.

## Scope

**Skill:** `campaign-planning-and-attribution`

**Request summary:** (fill in what the user asked for — e.g., "design campaign hierarchy for Q2 pipeline program" or "configure CCI first-touch and last-touch models")

---

## Context Gathered

Answer these before proceeding (from SKILL.md Before Starting section):

- **`enableCampaignInfluence2` value read from the retrieved `settings/Campaign.settings-meta.xml`:** [ ] true [ ] false — it defaults to **true**, so this is a read, not a switch to flip
- **`enableB2bmaCampaignInfluence2`:** [ ] true [ ] false — only meaningful when an external system publishes models
- **`enableAccountsAsCM`:** [ ] true [ ] false — changes what a CampaignMember can point at
- **Running user is a marketing user with a marketing licence?** [ ] Yes [ ] No — otherwise Campaign does not appear in `describeGlobal()` at all
- **Hierarchy depth the business needs:** _______ (governance number; no platform maximum is documented — confirm any ceiling in the org)
- **Attribution models in scope:** [ ] Primary Campaign Source [ ] Custom [ ] First Touch [ ] Last Touch [ ] Even Distribution [ ] Data-Driven
- **Model that will be the default (only one can be):** ___________
- **Writer for each model, and `isModelLocked` decision:** ___________

---

## Campaign Hierarchy Design

| Level | Campaign Name (example) | Campaign Type | Purpose |
|-------|------------------------|---------------|---------|
| 1 (Root) | | Program | Program-level ROI aggregation |
| 2 | | | Channel or sub-program |
| 3 | | | Tactic |
| 4 | | | (if needed) |
| 5 | | | (if needed) |

Add rows only up to the depth agreed above. No platform maximum is documented in the
Object Reference, the Metadata API guide, or the App Limits cheat sheet — do not design
against a number nobody can cite.

**Budgeted Cost owner (which level carries budget?):** Level ___

**ExpectedRevenue owner (which level carries forecast?):** Level ___

**Additional dimensions encoded as Campaign fields (not hierarchy levels):**
- Region field: ___________
- Product Line field: ___________
- Other: ___________

---

## Campaign Member Status Configuration

For each Campaign Type in scope, document the required status values:

Exactly one default and at least one responded value per campaign (API 39.0 and later).
Keep the default the least harmful value — an invalid status on load is coerced to it.

| Campaign Type | Status Value | Default? | Responded? | Sort | Notes |
|---|---|---|---|---|---|
| Email | Sent | Yes | No | 1 | Least harmful default |
| Email | Opened | No | No | 2 | |
| Email | Clicked | No | Yes | 3 | |
| Email | Unsubscribed | No | No | 4 | |
| Event | Invited | Yes | No | 1 | Least harmful default |
| Event | Registered | No | Yes | 2 | |
| Event | Attended | No | Yes | 3 | |
| Event | No Show | No | No | 4 | |
| (add rows as needed) | | | | | |

**Every writer of CampaignMember sends the status TEXT, not the status Id?** [ ] Confirmed

---

## Customizable Campaign Influence Model Plan

| Model Name | ModelType | `isDefaultModel` | `isModelLocked` | `recordPreference` | Written by | Use case |
|---|---|---|---|---|---|---|
| | Primary Campaign Source Model | | | | (never write to this one) | Ships with the org |
| | Custom Model | [ ] | [ ] | [ ] AllRecords [ ] RecordsWithAttribution | | Awareness credit |
| | Custom Model | [ ] | [ ] | [ ] AllRecords [ ] RecordsWithAttribution | | Conversion credit |

**Exactly one row above has `isDefaultModel` true?** [ ] Confirmed — it owns the Campaign
Influence related list on opportunities, the Influenced Opportunities related list on
campaigns, and the Campaign Statistics section. Everything else is report-only.

**Model lifecycle owner (deactivation deletes the model's rows):** ___________

**Contact Role approach** — the CCI-requires-contact-roles claim is not documented in the
official references; treat this as an org check, not a stated rule:
- [ ] Verified in this org that influence rows do / do not appear without Contact Roles
- [ ] Validation rule on Opportunity
- [ ] Flow automation
- [ ] Manual process / sales team checklist

---

## Attribution Reporting Plan

| Report / Dashboard | Object | Filter | Attribution Model | Consumer |
|-------------------|--------|--------|-------------------|---------|
| Program ROI Summary | Campaign | Root campaign | N/A — `Hierarchy*` fields | Marketing leadership |
| Attribution by Model | CampaignInfluence + Opportunity | CloseDate range, grouped by `ModelId` | All active models | Revenue ops |
| Member funnel | CampaignMember | Campaign, grouped by `Status` | N/A | Demand gen team |

**Field family chosen for hierarchy reporting:** [ ] `Hierarchy*` [ ] `Total*` — one family
per report, stated in the report description.

**Money column on CampaignInfluence is `RevenueShare`, not `Revenue`?** [ ] Confirmed

---

## Checklist

Before marking this work complete:

- [ ] Hierarchy depth is a stated governance number, not an assumed platform limit
- [ ] Parent Campaign records have Budgeted Cost and Expected Revenue set
- [ ] `enableCampaignInfluence2` read from the retrieved settings file, not assumed
- [ ] Exactly one model carries `isDefaultModel` true
- [ ] `recordPreference` is a deliberate choice per model
- [ ] `isModelLocked` matches the named writer for each model
- [ ] Nothing writes to the Primary Campaign Source model
- [ ] Every campaign has exactly one default status and at least one responded status
- [ ] Every CampaignMember writer sends status text, never a status Id
- [ ] Dashboards read `Hierarchy*` / `Total*`, never `ActualCost` as a rollup
- [ ] Model deactivation has a named owner and a change-control entry
- [ ] `scripts/check_campaign_planning_and_attribution.py` exits 0 on the plan and manifest
- [ ] Acceptance tests A1–A10 from `references/worked-examples.md` § 10 run and recorded

---

## Notes

Record any deviations from the standard pattern and the reason:

- 
- 
