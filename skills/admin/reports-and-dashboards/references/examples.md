# Examples: Reports and Dashboards

---

## Example: Pipeline Dashboard — 4 Components

**Audience:** VP of Sales, Sales Managers
**Business question:** "What's the health of our pipeline right now?"

### Component Design

| Component | Report | Chart Type | Metric | Why It Matters |
|-----------|--------|-----------|--------|---------------|
| Total Open Pipeline | Opportunities by Stage (Summary) | Funnel chart | Sum of Amount by Stage | Shows where deals are in the process at a glance |
| Deals Closing This Month | Opportunities closing ≤ 30 days (Tabular) | Table | Count + Sum Amount | Immediate revenue visibility |
| Pipeline by Owner | Opportunities by Owner (Summary) | Bar chart | Sum Amount per rep | Identify reps with thin or bloated pipelines |
| Win Rate (90 days) | Closed Opp by Stage - 90 days (Summary) | Gauge | Closed Won ÷ (Won + Lost) × 100 | Signal on deal quality |

### Running User Configuration
**Run as: logged-in user**

Why: A Sales Manager should see their team's pipeline (role hierarchy access), not all reps. A VP with "View All" sees everything. Using logged-in user respects the org's existing access model.

### Dashboard Filters

| Filter | Field | Applied To |
|--------|-------|-----------|
| Close Date Range | Opportunity.CloseDate | All components |
| Owner | Opportunity.OwnerId | Pipeline by Owner component |
| Record Type | Opportunity.RecordTypeId | All (so managers can toggle New Biz vs Renewal) |

---

## Example: Case Aging Report with Cross-Filter

**Business question:** "Which cases have been open more than 30 days AND have had no activity?"

**Report type:** Cases (Standard Report Type)
**Report format:** Summary

**Filters:**
- Status: not equal to "Closed"
- Created Date: less than or equal to TODAY() - 30

**Cross-filter:** Cases WITHOUT Activities (selects Cases that have no related Task or Event)

**Groupings:** By Owner, then by Priority

**Why cross-filter instead of a formula field:** A cross-filter handles "records WITHOUT a related record" declaratively, with no formula field needed. It directly queries the relationship.

**Columns to include:**
- Case Number
- Subject
- Owner
- Priority
- Created Date
- Age (formula: TODAY() - DATEVALUE(CreatedDate) — add as custom summary formula)
- Account Name

---

## Example: Account Health Report — Joining Multiple Objects

**Business question:** "Which accounts have high revenue but no open opportunities and no recent activity?"

**Approach: Joined Report** (combines multiple report types in one view)

**Block 1: Revenue Accounts**
- Report type: Accounts
- Filter: Annual Revenue > $500,000
- Show: Account Name, Revenue, Account Owner, Last Activity Date

**Block 2: Open Opportunities**
- Report type: Opportunities
- Filter: Stage NOT IN (Closed Won, Closed Lost)
- Show: Account Name, Opportunity Name, Amount, Stage

**Block 3: Recent Activities**
- Report type: Activities with Contacts and Accounts
- Filter: Activity Date > LAST 90 DAYS
- Show: Account Name, Subject, Activity Date

**Reading the result:** Accounts that appear in Block 1 but NOT in Block 2 or 3 are high-value accounts with no active deals and no recent engagement — highest risk for churn.

**Joined report limitation:** Max 2,000 rows per block. If there are more than 2,000 high-revenue accounts, you'll need to export and join outside Salesforce.

---

## Example: Bucketing to Replace Formula Fields in Reports

**Problem:** A Sales Manager wants to categorise opportunities by deal size without creating a formula field on the Opportunity object.

**Without bucketing:** Create `Deal_Size_Category__c` formula field on Opportunity → requires deployment.

**With bucketing:** Add a bucket column directly in the report:

```
Report column: Amount (currency)
Bucket column: Deal_Size_Category
  < $10,000    → "Small"
  $10,001–$50,000 → "Mid-Market"
  $50,001–$250,000 → "Enterprise"
  > $250,000   → "Strategic"
```

**Result:** The category appears as a column and grouping option in the report, with no metadata changes. The bucket exists only in the report — doesn't appear anywhere else.

**When to use bucketing:** Ad-hoc categorisation for reporting purposes only. When the category is useful for multiple reports or needs to appear in other parts of the org (list views, validation rules, flows), a formula field is better.
