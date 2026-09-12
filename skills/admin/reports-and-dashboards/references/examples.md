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

**Report type:** `CaseList` (the standard Case report type's API name — **not** `Cases`; see the
"How to read it" note below)
**Report format:** Summary

**Filters:**
- Status: not equal to "Closed"
- Created Date: less than or equal to TODAY() - 30

**Cross-filter:** Cases WITHOUT Activities (selects Cases that have no related Task or Event)

**Groupings:** By Owner, then by Priority

**Why cross-filter instead of a formula field:** A cross-filter handles "records WITHOUT a related record" declaratively, with no formula field needed. It directly queries the relationship.

**The same requirement expressed as metadata**, corrected against a live `sf project deploy
start --dry-run` (`reports/MOCK-DEPLOY-M5.md`, case-onboarding M5-S01, API 67.0) after three
guessed values in an earlier draft of this example were each proven wrong. `filter` narrows rows
on the Case itself; `crossFilters` removes Cases that have any related Activity:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Report xmlns="http://soap.sforce.com/2006/04/metadata">
    <columns>
        <field>STATUS</field>
    </columns>
    <columns>
        <field>CREATED_DATE</field>
    </columns>
    <description>Open Cases older than 30 days with no Activity, grouped by owner then priority, for the weekly aging review. The Escalated=True criterion is deferred to a runbook step (F-51) - its column code could not be confirmed offline.</description>
    <filter>
        <booleanFilter>1 AND 2</booleanFilter>
        <criteriaItems>
            <column>STATUS</column>
            <operator>notEqual</operator>
            <value>Closed</value>
        </criteriaItems>
        <criteriaItems>
            <column>CREATED_DATE</column>
            <operator>lessOrEqual</operator>
            <value>LAST_N_DAYS:30</value>
        </criteriaItems>
    </filter>
    <crossFilters>
        <operation>without</operation>
        <primaryTableColumn>CASES.ID</primaryTableColumn>
        <relatedTable>Task</relatedTable>
        <relatedTableJoinColumn>WhatId</relatedTableJoinColumn>
    </crossFilters>
    <format>Summary</format>
    <groupingsDown>
        <field>OWNER</field>
        <sortOrder>Asc</sortOrder>
    </groupingsDown>
    <groupingsDown>
        <field>PRIORITY</field>
        <sortOrder>Asc</sortOrder>
    </groupingsDown>
    <name>Case Aging Report</name>
    <reportType>CaseList</reportType>
</Report>
```

Read it as: `operation` is `without` (not a `!=` field filter), `relatedTable` names the child object, and `relatedTableJoinColumn` names the child field that joins back to the parent. A `<criteriaItems>` block *inside* `crossFilters` would sub-filter the child — "Cases without **open** Tasks" rather than "Cases without any Task"; up to five sub-filters are allowed. Omit it and the cross filter matches on existence alone.

> **UNVERIFIED (2026-09-04) — `CASES.ID` and `WhatId` are unconfirmed for this cross filter.**
> They follow the shape of the Metadata API guide's own cross-filter sample
> (`primaryTableColumn` `ACCOUNT_ID`, `relatedTable` `Case`, `relatedTableJoinColumn` `Account`),
> but the guide publishes no codes for a Cases-to-Activities cross filter, and unlike the
> `reportType`/grouping/column values below, this cross filter was never put through the
> case-onboarding M5-S01 dry-run (its built report carries no `crossFilters` block — see
> `reports/MOCK-DEPLOY-M5.md`). Retrieve a working report before deploying this snippet. The
> `operation` / `relatedTable` / `relatedTableJoinColumn` structure itself is from the guide's
> field table.

### How to read it — four wrong guesses, proven wrong live, in the order the org surfaced them

Three earlier draft values in this exact example — `reportType`, a grouping, and a column overlap
- each passed local review and each failed only when actually deployed. In order:

1. `<reportType>Cases</reportType>` → `invalid report type`. The standard Case report type's API
   name is **`CaseList`**, not the object name. Fixed above.
2. With `CaseList` in place, `<groupingsDown><field>USERS.NAME</field>` (copied from the Metadata
   API guide's own unrelated Report sample) → `Grouping: Invalid value specified: USERS.NAME`.
   **`OWNER`** was accepted instead. Fixed above.
3. With `OWNER` as the first grouping, a draft that also grouped and displayed `PRIORITY` in
   `<columns>` failed with `You can't include groupings in the selected columns list: PRIORITY`
   — a field cannot be both a `groupingsDown` entry and a `columns` entry on the same report.
   Fixed above by keeping `PRIORITY` as a grouping only.
4. The description itself failed first, before any of the above: an earlier draft used the
   `<description>` field to carry a build/UNVERIFIED note and hit `Value too long for field:
   Description maximum length is:255`. The description above is 224 characters — under the
   255-character hard limit and under the 235-character advisory headroom this skill's checker
   also flags (RPT-DESC-01 / RPT-DESC-02).

None of these four limits or names is stated in the Metadata API Developer Guide — all four are
`UNVERIFIED (2026-09-04)` in the guide and proven only by the live dry-run above (F-49/F-50,
`reports/MOCK-DEPLOY-M5.md`). Run `python3 scripts/check_report_inventory.py --manifest-dir <dir>`
before deploying: it now catches #1 (RPT-TYPE-01), #3 (RPT-GRP-01), and the description length
(#4, RPT-DESC-01/02) offline. It cannot catch #2 in general — see the escalated-column note below.

**The Escalated criterion is deliberately absent, and that's the honest answer (F-51).** The
business question really needs `IsEscalated = true`, not just "no Activity." Five candidate
column codes — `ESCALATED`, `IS_ESCALATED`, `CASES.ESCALATED`, `ISESCALATED`, `CASE_ESCALATED` —
were each rejected live with `filters-criteriaItems-column: Invalid value specified`, and no
cited skill or guide states the correct one. Rather than guess a sixth time, this example ships
without that filter and records it as a runbook step: deploy first, then either (a) add
"Escalated = True" in the report builder UI and let it write the code, or (b) once that filter
exists on one saved report, retrieve it and copy the code into source. This skill's own checker
flags exactly this shape generically — RPT-COL-01 (INFO) fires on any `criteriaItems`/`columns`
code that isn't one of the report's own grouping fields or already confirmed for this report
type, since column codes are report-type-specific and cannot be verified offline in general.

**Columns to include (labels — not the report column codes above; retrieve those separately for
each field you add):**
- Case Number
- Subject
- Owner
- Priority
- Created Date
- Age (formula: TODAY() - DATEVALUE(CreatedDate) — add as custom summary formula)
- Account Name

Note the trap this example itself walked into: `Priority` is used as a **grouping** in the
metadata above. Per RPT-GRP-01 (F-50), it cannot *also* appear as a `<columns>` entry in the same
report — group by it, or display it as a column, not both.

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
