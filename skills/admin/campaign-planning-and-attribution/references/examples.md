# Examples — Campaign Planning And Attribution

Three worked designs and one anti-pattern. For the full end-to-end build — deployable
XML, package.xml, retrieve/deploy commands and acceptance tests — see
`references/worked-examples.md`.

## Example 1: Multi-Level Campaign Hierarchy for a Quarterly Demand-Gen Program

**Context:** A B2B SaaS company runs a "Q1 Pipeline Drive" that spans three channels: a webinar series, a paid LinkedIn campaign, and a nurture email track. Marketing ops wants a single Campaign record to show total program ROI without manually aggregating channel spend.

**Problem:** Without a hierarchy, three separate Campaign records each carry their own `ActualCost` and `AmountWonOpportunities`. There is no native way to aggregate them into a program-level view in Salesforce reports without manual spreadsheet work.

**Solution:**

```text
Q1 Pipeline Drive          (Type: Other,         ParentId: null)
├── Q1 Webinar Series      (Type: Webinar,       ParentId: Q1 Pipeline Drive)
├── Q1 LinkedIn Paid       (Type: Advertisement, ParentId: Q1 Pipeline Drive)
└── Q1 Nurture Track       (Type: Email,         ParentId: Q1 Pipeline Drive)
```

Configuration steps:

1. Create the parent Campaign "Q1 Pipeline Drive". Set `BudgetedCost = 50000` and `ExpectedRevenue = 300000` — both are documented as the campaign's own budget and expected generation (object_reference.txt:57146–57152, 57255–57271).
2. Create the three child Campaigns with `ParentId` pointing to the parent. `ParentId` is the lookup to `Campaign`; `ParentCampaign` is the read-only "campaign above the selected campaign in the campaign hierarchy" (object_reference.txt:57634–57653).
3. As spend is confirmed per channel, populate `ActualCost` on each **child** Campaign.
4. Build the program report on the **hierarchy** fields, not the short names:

```sql
SELECT Id, Name, Type, IsActive, ParentId,
       ActualCost,                       -- this campaign's own spend
       HierarchyActualCost,              -- Total Actual Cost in Hierarchy
       HierarchyBudgetedCost,
       HierarchyExpectedRevenue,
       HierarchyAmountAllOpportunities,
       HierarchyAmountWonOpportunities,  -- Value Won Opportunities in Hierarchy
       HierarchyNumberOfResponses
FROM Campaign
WHERE Name = 'Q1 Pipeline Drive'
```

ROI on the program is then `(HierarchyAmountWonOpportunities - HierarchyActualCost) / HierarchyActualCost` — a report formula, computed at display time.

**Why it works:** The `Hierarchy*` family is defined as calculated fields "for the campaigns in a campaign hierarchy" (object_reference.txt:57273–57359), so the aggregation is the platform's, not yours. What breaks the naive version is naming: `ActualCost` on the parent is "the amount of money spent to run the campaign" — the parent alone (object_reference.txt:57100–57105). A parent whose own spend is zero shows zero, and the report looks broken. A parallel family, `TotalAmountAllWonOpportunities` / `TotalNumberofResponses` and siblings (object_reference.txt:57704–57810), reports the same hierarchy; pick one family per report and note which in the description.

---

## Example 2: First-Touch and Last-Touch Dual-Model CCI Configuration

**Context:** A revenue operations team needs to report on which campaigns "opened the door" (first touch) vs. which campaigns "closed the deal" (last touch). They need both views simultaneously to justify top-of-funnel awareness spend vs. bottom-of-funnel conversion spend.

**Problem:** Only one model can be the default, and only the default model's records appear on campaigns and opportunities. A design that expects both views in the page layout will disappoint whichever model loses.

**Solution:**

1. Retrieve `settings/Campaign.settings-meta.xml` and read `enableCampaignInfluence2`. It defaults to true (api_meta.txt:111568–111571), so the usual first step is confirming, not enabling.
2. Deploy two `CampaignInfluenceModel` files. `isDefaultModel` is required on both; exactly one is true. Set `isModelLocked` true so the API is the single writer, and choose `recordPreference` deliberately — `RecordsWithAttribution` suppresses zero-credit rows (api_meta.txt:31920–31926).
3. The default model drives three UI surfaces and nothing else: the Campaign Influence related list on opportunities, the Influenced Opportunities related list on campaigns, and the Campaign Statistics section on campaigns (object_reference.txt:58055–58066). Both models are equally queryable.
4. Verify with SOQL. The attributed-money field is `RevenueShare`; there is no `Revenue` field on this object (object_reference.txt:57987–57992):

```sql
SELECT Model.DeveloperName, Model.ModelType, Model.IsDefaultModel,
       Campaign.Name, Opportunity.Name, Opportunity.Amount,
       Influence, RevenueShare
FROM CampaignInfluence
WHERE Opportunity.StageName = 'Closed Won'
ORDER BY Model.DeveloperName, RevenueShare DESC
```

5. Build **one** custom report type on `CampaignInfluence` joined to `Opportunity`, and group by `ModelId` in the report. Two report types, one per model, is duplicated maintenance for a column difference.

**Why it works:** CCI writes independent `CampaignInfluence` rows per model per opportunity, and `ModelId` is a first-class filterable field, so both views coexist in data. What does not coexist is UI prominence — that is the `isDefaultModel` decision, and it belongs in the design document rather than in a deploy diff. Note that `CampaignInfluenceModel` is read-only as an sObject (supported calls are `describeSObjects()`, `query()`, `retrieve()` only, object_reference.txt:58011–58012), so the model itself is created by deploy or Setup, never by DML.

---

## Example 3: Repairing Campaign Member Statuses After a Silent Coercion

**Context:** An org loads webinar attendance from an events platform each week. Attribution looks thin — few members show as responded, though the events platform reports high attendance.

**Problem:** The load sends `Status = 'Attended'`, but the webinar campaigns were cloned from a template whose status set is `Sent` / `Responded`. Nothing errored. Every row inserted with `Status = 'Sent'`, because the API "assigns the default status to the Status field" when the supplied value is not valid for that campaign (object_reference.txt:58572–58577). The success count was 100% each week.

**Solution:**

First, find every campaign whose status set cannot accept the load. This is the diagnostic, not a fix:

```sql
SELECT CampaignId, Campaign.Name, Label, IsDefault, HasResponded, SortOrder
FROM CampaignMemberStatus
WHERE Campaign.Type = 'Webinar'
  AND Campaign.IsActive = true
ORDER BY CampaignId, SortOrder
```

Then define the intended set once, in the plan record, so it is reviewable:

```yaml
member_status_sets:
  - set_id: event
    applies_to_campaign_type: Webinar
    statuses:
      - label: Invited
        is_default: true      # least harmful default: a coercion under-reports
        has_responded: false
        sort_order: 1
      - label: Registered
        is_default: false
        has_responded: true
        sort_order: 2
      - label: Attended
        is_default: false
        has_responded: true
        sort_order: 3
      - label: No Show
        is_default: false
        has_responded: false
        sort_order: 4
```

Apply it per campaign — `CampaignMemberStatus` is an sObject, not a metadata type, so this is record work and cannot be deployed. Order matters: promote `Invited` to default **before** removing anything, because a status that is the default or in use cannot be deleted (object_reference.txt:58609), and every campaign must have a default and at least one responded status from API version 39.0 onward (object_reference.txt:58627, 58636).

Finally, re-drive the affected members by updating `Status` with the **text** value — an Id from `CampaignMemberStatus` coerces on every row (object_reference.txt:58504–58513) — and reconcile by counts per status, never by success count.

**Why it works:** `HasResponded` on the member is read-only and is moved only by `Status`; `Campaign.NumberOfResponses` and `HierarchyNumberOfResponses` count members "with a Member Status equivalent to 'Responded'" (object_reference.txt:57585–57591, 57353–57359). Fixing the status vocabulary is therefore the whole fix — nothing downstream needs recalculating by hand.

---

## Anti-Pattern: Automating on a Calculated Campaign Field

**What practitioners do:** Build a Flow or Apex trigger that fires when a parent Campaign's `HierarchyAmountWonOpportunities` or `ActualCost` crosses a threshold, to send an alert or update a milestone record.

**What goes wrong:** The `Hierarchy*` and `Total*` fields are documented as *calculated* fields (object_reference.txt:57273–57359, 57704–57810). The Object Reference publishes no refresh cadence or SLA for them, so an automation that treats a change on one as an event has no contract to rely on — UNVERIFIED (2026-09-05): the widely-repeated "updates every few hours" figure has no source in the extracts. Worse, `HierarchyNumberOfLeads` and `HierarchyNumberOfResponses` are typed `currency` despite holding counts (object_reference.txt:57338, 57354), so a comparison written against an `Integer` variable behaves unexpectedly.

**Correct approach:** Trigger from the record that actually changes — an Opportunity reaching Closed Won, or a `CampaignMember` status change — and walk up to the campaign from there. Read the hierarchy fields when a human or a report asks for them, not as an event source.
