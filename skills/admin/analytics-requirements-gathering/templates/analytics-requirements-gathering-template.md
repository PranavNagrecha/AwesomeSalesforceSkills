# Analytics Requirements Gathering — Work Template

Use this template to capture CRM Analytics requirements before any dataset or dashboard is built.

## Scope

**Skill:** `analytics-requirements-gathering`

**Project Name:** (fill in)
**Primary Stakeholder(s):** (fill in)
**CRM Analytics License:** Confirmed / Not confirmed
**Decision:** CRM Analytics required / Standard Reports sufficient — Rationale: ______

---

## CRM Analytics vs Standard Reports Decision

| Factor | Applies? | Notes |
|---|---|---|
| More than 2 objects must be joined | Yes / No | |
| External data (Snowflake, BigQuery, S3) needed | Yes / No | |
| Predictive scoring or trend forecasting needed | Yes / No | |
| Row-level security beyond standard sharing | Yes / No | |
| Dataset aggregates exceed 2,000 rows | Yes / No | |
| **Decision** | **CRM Analytics / Standard Reports** | |

---

## Data Source Mapping Matrix

| Data Source Name | Source Type | Connection Mechanism | Fields Needed | Refresh Frequency | Incremental? |
|---|---|---|---|---|---|
| | Salesforce Object Sync / External Connector / Data Cloud / CSV | Named Credential / Direct sync | (list fields) | Daily / Hourly / On-demand | Yes / No |

---

## Transformation Requirements

| Transformation | Description | Source Fields | Target Field |
|---|---|---|---|
| Join | Account + Opportunity on AccountId | Account.AccountId, Opportunity.AccountId | (joined dataset) |
| Computed field | FiscalQuarter from CloseDate | CloseDate | FiscalQuarter__c |
| Field rename | Normalize display names | | |
| Filter | Exclude inactive accounts | IsActive__c == false | (filtered) |

---

## Audience Matrix

| User Role | Data Rows Accessible | Row-Level Security Mechanism | Dashboard View |
|---|---|---|---|
| | All / Own records / Team records / Custom | Sharing inheritance / SAQL predicate / Separate dashboard | Same as others / Unique layout |

**SAQL predicates (if applicable):**
- Role: Sales Rep → `'OwnerId' == "$User.Id"`
- Role: Manager → `'Region__c' == "$UserAttribute.Region__c"`

---

## Drill-Down Path Requirements

| Summary Visualization | Drill-Down Level 1 | Drill-Down Level 2 |
|---|---|---|
| Revenue by Region | Revenue by Owner within Region | Opportunity list for that Owner |

---

## Review Checklist

- [ ] CRM Analytics vs standard Reports decision documented
- [ ] CRM Analytics license confirmed
- [ ] All data sources documented with type and connection mechanism
- [ ] Field-level requirements captured for each data source
- [ ] Transformation requirements specified (joins, computed fields, renames)
- [ ] Audience matrix complete with row-level security mechanism
- [ ] Drill-down paths documented
- [ ] Refresh cadence and incremental refresh requirements specified
