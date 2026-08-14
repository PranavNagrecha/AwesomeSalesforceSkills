# Sales Reporting Data Model — Work Template

Use this template when designing or documenting sales reporting architecture decisions for a Salesforce org.

## Scope

**Skill:** `sales-reporting-data-model`

**Request summary:** (fill in what the stakeholder asked for)

**Reporting time horizon:**
- [ ] Rolling short-term trend (≤ 3 months) → candidate: Historical Trend Reporting
- [ ] Point-in-time archive (> 3 months or multi-year) → candidate: Reporting Snapshots
- [ ] Exception / gap analysis → candidate: Custom Report Type with "without" join
- [ ] Combination of the above

---

## Context Gathered

Complete before recommending or implementing:

- **HTR activation state**: Is HTR enabled in Setup > Historical Trend Reporting?
  - [ ] Enabled — note which objects and fields are currently tracked
  - [ ] Not enabled — note activation date if being enabled now
- **Current tracked fields on Opportunity** (if HTR is active): list them here
- **Open pipeline row count** (if Reporting Snapshots are under consideration): approximate count of Opportunities in the intended source report scope
  - Count: _____ (a run inserts at most 2,000 new records into the target object; the surplus is dropped with a partial error in Run History)
- **Longest required history window**: _____ months / years
- **Multi-currency org?** Yes / No
- **Running User candidate for Reporting Snapshot** (should be a service/integration user, not an employee):

---

## Mechanism Selection

| Requirement | Selected Mechanism | Rationale |
|---|---|---|
| Near-term stage/amount trend (≤ 90 days) | | |
| Pipeline archive (> 90 days) | | |
| Gap / exception report | | |
| Multi-year QBR comparison | | |

---

## Historical Trend Reporting Configuration (if applicable)

**Object:** Opportunity (or other: _______)

**Fields to track** (max 8 total; 5 standard + 3 custom on Opportunity):

| Field Label | API Name | Standard or Custom |
|---|---|---|
| | | |
| | | |
| | | |

**Report type to use:** Opportunities with Historical Trending

**Retention window:** previous 3 months plus the current month (same for every trending-enabled object; Historical Trending in Pipeline Inspection extends Opportunity to 12 months) — document for stakeholders

---

## Reporting Snapshot Design (if applicable)

**Source report:**
- Report name:
- Report type: Tabular / Summary
- Filters applied (to keep new records per run below 2,000):
- Confirmed new records per run at design time: _____

**Target custom object:**

| Object label | API name |
|---|---|
| | |

**Field mapping:**

| Source Report Column | Target Field Label | Target Field API Name | Field Type |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

**Schedule:**
- Frequency: Daily / Weekly / Hourly
- Run time (org timezone): _____
- Running User (service account): _____

**Monitoring plan:** (how will failed or truncated runs be detected?)

---

## Custom Report Type Design (if applicable)

**Primary object:** _____

**Relationship chain:**

| Step | Child Object | Join Type | Notes |
|---|---|---|---|
| 1 | | With / Without | |
| 2 | | With / Without | |
| 3 | | With / Without | |

**CRT deployment status:** Deployed (required before users can access)

**Test case — gap record:** (name a specific record with no children to validate "without" join works)

---

## Checklist

Copy from SKILL.md review checklist and tick items as complete:

- [ ] HTR enabled and fields selected within 8-field cap
- [ ] HTR not enabled retroactively for a period already needed
- [ ] Reporting Snapshot expected new records per run confirmed at or below 2,000 (target-object insert cap)
- [ ] Snapshot target object uses Currency/Date/Percent types (not Text) for non-text fields
- [ ] Snapshot schedule active; Running User is a service account
- [ ] Snapshot run history checked after first execution
- [ ] CRT status set to "Deployed"
- [ ] CRT join type validated with known test data
- [ ] Snapshot reports include `Snapshot_Date__c` filter
- [ ] Multi-currency field types confirmed if applicable

---

## Decisions and Deviations

Record any deviations from the standard patterns and the rationale:

(e.g., "Used Apex scheduled batch instead of Reporting Snapshot because pipeline scope exceeds 2,000 new records per run")
