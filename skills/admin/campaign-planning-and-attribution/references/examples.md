# Examples — Campaign Planning And Attribution

## Example 1: Multi-Level Campaign Hierarchy for a Quarterly Demand-Gen Program

**Context:** A B2B SaaS company runs a "Q1 Pipeline Drive" that spans three channels: a webinar series, a paid LinkedIn campaign, and a nurture email track. Marketing ops wants a single Campaign record to show total program ROI without manually aggregating channel spend.

**Problem:** Without a hierarchy, three separate Campaign records each carry their own `ActualCost` and `AmountWonOpportunities`. There is no native way to aggregate them into a program-level view in Salesforce reports without manual spreadsheet work.

**Solution:**

Create the following Campaign structure in Salesforce:

```
Q1 Pipeline Drive (Type: Program, Level 1)
├── Q1 Webinar Series (Type: Event, Level 2)
├── Q1 LinkedIn Paid (Type: Advertising, Level 2)
└── Q1 Nurture Track (Type: Email, Level 2)
```

Configuration steps:
1. Create the parent Campaign "Q1 Pipeline Drive". Set `BudgetedCost = 50000` and `ExpectedRevenue = 300000`.
2. Create the three child Campaigns with `ParentId` pointing to the parent.
3. As spend is confirmed per channel, populate `ActualCost` on each child Campaign.
4. Build a Campaign report filtered to the parent Campaign (using hierarchy filter) using rollup fields:
   - `ActualCost` (summed from children automatically)
   - `AmountWonOpportunities` (summed from children)
   - ROI formula: `(AmountWonOpportunities - ActualCost) / ActualCost`

**Why it works:** Salesforce's Campaign Hierarchy rollup mechanism aggregates `ActualCost`, `NumberOfLeads`, `NumberOfContacts`, `NumberOfResponses`, `AmountAllOpportunities`, and `AmountWonOpportunities` from all descendants up to the root. No custom code is required. The rollup is batch-updated by Salesforce, so the parent record always reflects the cumulative sum of all child records.

---

## Example 2: First-Touch and Last-Touch Dual-Model CCI Configuration

**Context:** A revenue operations team needs to report on which campaigns "opened the door" (first touch) vs. which campaigns "closed the deal" (last touch). They need both views simultaneously to justify top-of-funnel awareness spend vs. bottom-of-funnel conversion spend.

**Problem:** Standard Campaign Influence (non-customizable) only supports one active model at a time. Running two separate analyses requires exporting data outside Salesforce. There is also no way to weight campaigns differently in standard influence.

**Solution:**

Enable and configure Customizable Campaign Influence with two models:

1. Navigate to Setup > Campaign Influence > enable "Customizable Campaign Influence".
2. Create Model 1 — "First Touch":
   - Influence Type: Primary Campaign Source (first campaign contact was a member of)
   - Mark as Primary Model
3. Create Model 2 — "Last Touch":
   - Influence Type: Campaign Last Touch (most recent campaign activity before opportunity creation or close)
4. Ensure all Opportunities have Contact Roles populated. This can be automated via a Flow that creates a Contact Role when a Contact's Campaign Member status reaches "Responded".
5. Once Opportunities are created, query `CampaignInfluence` records to verify:

```soql
SELECT CampaignId, OpportunityId, ContactId, Influence, Revenue, ModelId
FROM CampaignInfluence
WHERE Opportunity.StageName = 'Closed Won'
ORDER BY OpportunityId, ModelId
```

6. Build two separate Campaign Influence report types — one for each model — and display them in a side-by-side dashboard.

**Why it works:** CCI creates separate `CampaignInfluence` records per model per opportunity. Each model's records are independent, so first-touch and last-touch attribution can be reported simultaneously without interference. The `Revenue` field on each `CampaignInfluence` record reflects the attributed portion of the Opportunity amount per that model.

---

## Example 3: Campaign Member Status Alignment for MCAE Attribution

**Context:** An org uses MCAE to send emails and drive webinar registrations. Attribution data is sparse — many Opportunities show zero campaign influence despite strong email engagement preceding the deal.

**Problem:** The Campaign Member Status picklist for the Email Campaign Type was never configured. MCAE attempted to write "Opened" and "Clicked" member statuses but failed silently because those values did not exist in the picklist. As a result, engagement was never recorded as Campaign Member records, and CCI had no member data to attribute.

**Solution:**

For each Campaign Type that MCAE writes to, configure the following statuses in Setup > Campaign Member Statuses:

| Status Value | Responded | Salesforce Default |
|---|---|---|
| Sent | No | Yes |
| Opened | No | No (must add) |
| Clicked | No | No (must add) |
| Responded | Yes | No (must add) |
| Unsubscribed | No | No (must add) |

Configuration steps:
1. Navigate to Setup > Campaign Member Statuses.
2. For the Email Campaign Type, add: Sent, Opened, Clicked, Responded, Unsubscribed.
3. Set `Responded = true` on "Responded" only.
4. Re-sync MCAE campaign membership for affected campaigns (MCAE > Campaigns > Sync).
5. Verify `CampaignMember` records appear with the correct statuses.

**Why it works:** MCAE writes Campaign Member records with specific status strings. If the status string does not exist in the picklist, MCAE drops the record. Once statuses are correctly configured, MCAE retroactively writes previously missing member records on re-sync, which then feeds CCI attribution.

---

## Anti-Pattern: Using Parent Campaign `AmountWonOpportunities` in Real-Time Automation

**What practitioners do:** Build a Flow or Apex trigger that fires when a parent Campaign's `AmountWonOpportunities` exceeds a threshold (e.g., to send an alert or update a milestone record).

**What goes wrong:** `AmountWonOpportunities` on a Campaign is a rollup summary field updated by Salesforce's batch scheduler, not a formula field. It does not update in real time when a child opportunity closes. The Flow or trigger fires late or not at all during the campaign's active period, making the automation unreliable. Teams discover the lag only after a milestone alert fails to fire during a live campaign.

**Correct approach:** Trigger automation on the Opportunity close event directly (using a Flow on the Opportunity object, stage = Closed Won), then look up the parent Campaign hierarchy from the Opportunity's Campaign field. Do not rely on Campaign rollup fields as an event source.
