# Examples — Donor Lifecycle Requirements

## Example 1: LYBUNT Re-engagement Campaign Design

**Context:** A community foundation has 1,200 donors who gave in the previous fiscal year but have not given in the current year (LYBUNT). The major gifts team wants to prioritize re-engagement based on prior year giving amount.

**Problem:** The team runs the NPSP LYBUNT report but does not know how to segment re-engagement efforts or track outcomes of their outreach.

**Solution:**

```text
LYBUNT Re-engagement Workflow:
1. Run NPSP LYBUNT report (Reports > Fundraising > LYBUNT)
   Filter: Last gift $500+ (npsp__LastOppAmount__c >= 500)
   
2. From report, mass-action: Add to Campaign "FY2026 LYBUNT Re-engagement"
   Campaign Type: Direct Mail/Phone
   Start Date: October 1, 2026
   
3. Create three Campaigns for tiered outreach:
   - Tier 1: $5,000+ LYBUNT → Personal phone call from ED
   - Tier 2: $500-$4,999 LYBUNT → Personalized letter + 2 follow-up calls
   - Tier 3: $100-$499 LYBUNT → Email series (3 touches)

4. Create Engagement Plans per tier with task sequences

5. Track re-engagement: Report on Campaign Member → Opportunity linked to campaign
   Measure: Re-engagement rate (% who gave), re-engagement revenue total
```

**Why it works:** NPSP's LYBUNT report directly surfaces the target population using built-in rollup fields. Campaign-based tracking connects re-engagement outreach to resulting gifts, enabling ROI measurement on the re-engagement program.

---

## Example 2: Major Gift Pipeline with Moves Management

**Context:** A university advancement office wants to build a Salesforce-based major gift cultivation pipeline showing each prospect's cultivation stage, next steps, and projected close amounts.

**Problem:** Gift officers track cultivation in personal spreadsheets. Prospect assignments, cultivation stage, and ask amounts are not visible to the development director for portfolio reviews.

**Solution:**

```text
Moves Management Configuration:

1. Opportunity Record Type: "Major Gift Solicitation"
   Stage picklist: Prospect Identified → In Cultivation → Proposal Drafted 
                   → Ask Made → Pledge Received → Closed Won / Closed Lost

2. Opportunity Sales Process: restrict to Major Gift stages only

3. Required fields at stage transitions:
   - "Ask Made" → Amount (proposed ask) and Close Date required
   - "Pledge Received" → Amount and pledge schedule required

4. Path component on Opportunity layout with coaching text per stage

5. Pipeline Report:
   Object: Opportunity
   Filters: Record Type = Major Gift, Stage != Closed Won/Lost
   Group by: Owner (gift officer), Stage
   Fields: Name, Account, Amount, Close Date, Next Step
   
6. Weekly portfolio review: director reviews open pipeline by officer
```

**Why it works:** NPSP Opportunities provide the financial pipeline view that cultivation Contacts and Activities alone cannot. Stage progression is visible to the entire team. The Pipeline Report replaces spreadsheet-based portfolio tracking with a live, accurate view.

---

## Anti-Pattern: Using Contact Activities as the Sole Cultivation Tracking Method

**What practitioners do:** Gift officers log every cultivation interaction as a Task or Event on the Contact record and consider this sufficient moves management. There is no Opportunity record until a pledge is received.

**What goes wrong:** Development directors cannot see the pipeline because there are no Opportunity records with projected amounts and close dates. Portfolio reviews require manual aggregation of Activity counts per contact. There is no financial projection for annual budgeting. Cultivation stages are not visible without reading through unstructured Activity notes.

**Correct approach:** Create an Opportunity record when a prospect enters formal cultivation (not just when a gift is expected). Use the Opportunity Stage to track cultivation progress, the Amount field for projected ask, and the Close Date for expected decision timeline. Log cultivation Activities on both the Contact AND the linked Opportunity for full relationship history.
