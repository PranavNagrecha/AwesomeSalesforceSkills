# CRM Analytics App Creation — Work Template

Use this template when creating a new CRM Analytics application.

## Scope

**Skill:** `crm-analytics-app-creation`

**App name:** (fill in)

**Use case:** (e.g., Sales Pipeline, Service Metrics, Executive Summary)

**Target users / profiles:** (fill in)

**Data sources required:** (list Salesforce objects or external sources)

## Pre-Creation Checklist

- [ ] CRM Analytics license confirmed for admin creating the app
- [ ] CRM Analytics permission set assigned to target users
- [ ] Required Salesforce objects identified for Data Sync

## App Structure Plan

| Component | Name | Description |
|---|---|---|
| App | | |
| Dataset | | Objects: |
| Lens 1 | | Grouping: / Measure: |
| Lens 2 | | Grouping: / Measure: |
| Dashboard | | Lenses used: |

## Data Sync Configuration

| Object | Sync Enabled? | Sync Schedule |
|---|---|---|
| | [ ] | |
| | [ ] | |

## Dataset Configuration

| Dataset Name | Recipe or Dataflow? | Input Objects | Refresh Schedule |
|---|---|---|---|
| | [ ] Recipe / [ ] Dataflow | | |

## Security Configuration

**App sharing:**

| User / Group | Role (Viewer/Editor/Manager) |
|---|---|
| | |
| | |

**Row-level security:**

- [ ] Security predicate configured on dataset
- [ ] Predicate: `_____`
- [ ] Tested as non-admin user — correct rows visible

OR

- [ ] Sharing inheritance enabled (Account/Case/Contact/Lead/Opportunity only, max 3000 rows)

## Post-Creation Verification

- [ ] Non-admin test user can see app
- [ ] Non-admin test user sees correct data (not all rows)
- [ ] Dataset refreshes on schedule
- [ ] Dashboard filters work correctly
- [ ] Faceting tested (same-dataset widgets only)

## Notes

(Record any deviations from the standard setup and reasons.)
