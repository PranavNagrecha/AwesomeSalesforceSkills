# Enterprise Territory Management — Territory Model Design Template

Use this template when designing a new territory model or documenting an existing one for review or deployment.

---

## 1. Model Overview

| Field | Value |
|---|---|
| Model Label (`<name>` in the XML) | _____________ |
| Model Developer Name (file name; version-stamp it, e.g. `FY26_NA`) | _____________ |
| State of that developer name in the TARGET org (`SELECT DeveloperName, State FROM Territory2Model`) | Not present / Planning / Active / **Archived — blocks the deploy** |
| Release mechanism | Source deploy (change sets and packaging are not available for these types) |
| Deploying user holds Manage Territories? | Yes / No |
| Model Purpose | _____________ (e.g., "FY26 North America field sales and named account coverage") |
| Target Activation Date | _____________ |
| Activation Window | _____________ (e.g., "Saturday 10 PM–12 AM PST") |
| Current State | Planning / Active / Archived |

---

## 2. Territory Types

Define at least one territory type before creating territories. **The highest priority integer wins** opportunity territory assignment, and priority values must be unique across types. A tie at the top priority assigns no territory to the opportunity at all.

| Territory Type Name | Developer Name | Priority (unique; highest wins) | Description / Use Case |
|---|---|---|---|
| _____________ | _____________ | _____ | _____________ |
| _____________ | _____________ | _____ | _____________ |
| _____________ | _____________ | _____ | _____________ |

---

## 3. Territory Hierarchy

Map out the parent-child structure. Each territory must have a territory type assigned. Recommended maximum depth: 5–6 levels.

```
[Root Territory Name] — Type: _____________
├── [Level 1 Territory] — Type: _____________
│   ├── [Level 2 Territory] — Type: _____________
│   └── [Level 2 Territory] — Type: _____________
├── [Level 1 Territory] — Type: _____________
│   ├── [Level 2 Territory] — Type: _____________
│   └── [Level 2 Territory] — Type: _____________
└── [Overlay Root, if applicable] — Type: _____________
    ├── [Overlay Territory 1] — Type: _____________
    └── [Overlay Territory 2] — Type: _____________
```

Total territory count: _____ — record the ceiling you confirmed and where you confirmed it: _____________ (the widely repeated 1,000 / 20,000 figures are not in the App Limits Cheat Sheet or the Metadata API and Object Reference sections; verify in Salesforce Help before designing to them)

---

## 4. Account Assignment Rules

For each territory, document the filter criteria that will drive automatic account assignment.

A `Territory2Rule` lives in the model's `rules/` folder and belongs to the **model**. Each territory that should use it needs its own `ruleAssociations` entry naming the rule. A rule with no association deploys cleanly and assigns nothing.

Valid `operation` values: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, `within` (DISTANCE only). A rule holds at most 10 rule items.

| Rule Developer Name | Field | Operation | Value(s) | `active`? | Associated territories (`inherited` per entry) |
|---|---|---|---|---|---|
| _____________ | BillingCountry | equals | _____________ | true / false | _____________ |
| _____________ | Industry | equals | _____________ | true / false | _____________ |
| _____________ | _____________ | _____________ | _____________ | true / false | _____________ |
| _____________ | _____________ | _____________ | _____________ | true / false | _____________ |

`booleanFilter` (numbering starts at 1, contiguous, order derived from position in the XML): _____________

Notes on rule design:
- If an account matches rules for multiple territories, it will be assigned to ALL matching territories. Confirm this is intentional.
- Accounts with `IsExcludedFromRealign` = true are never evaluated. Confirm no in-scope account carries it.
- Confirm `Territory2Settings.tm2BypassRealignAccInsert` is false, or accounts created by insert jobs stay unassigned with no error.
- Rules are not retroactive. After creating or modifying rules, manually run assignment at the model level to apply to existing accounts.
- Test rule coverage in preview mode before activation.

---

## 5. User Territory Memberships

List users and their territory assignments. Users can be members of multiple territories.

`UserTerritory2Association` is data, not metadata — load it with Data Loader or Apex after the model exists. `RoleInTerritory2` is a picklist: `Owner`, `Administrator`, `Sales Rep`. The object supports no `update()` call, so a role change is a delete plus an insert.

| User Name | Territory Developer Name | `RoleInTerritory2` | `IsActive` | Notes |
|---|---|---|---|---|
| _____________ | _____________ | Sales Rep | true | _____________ |
| _____________ | _____________ | Administrator | true | Forecast user; manages sub-territory rollup |
| _____________ | _____________ | _____________ | true | _____________ |

Is `Territory2Settings.tm2EnableUserAssignmentLog` on, and has a model been activated? (Both are required before `UserTerritory2AssocLog` records anything.) Yes / No: _______

---

## 6. Access Levels (fields on each Territory2, not Territory2ObjSharingConfig)

These are elements on each `Territory2` component. Omit an element entirely to inherit the matching `default*AccessLevel` from `Territory2Settings`. Metadata API spellings only — `Read Only`, `Read/Write`, `Owner` and `Private` are UI/SOAP values and are invalid in XML.

| Element | Valid values | OWD constraint from the guide | Chosen value |
|---|---|---|---|
| `accountAccessLevel` | Read, Edit, All | If Account sharing is Public Read/Write, only Edit and All are valid | _____________ |
| `opportunityAccessLevel` | None, Read, Edit | Specify no value if cases/opportunities are Public Read/Write | _____________ |
| `contactAccessLevel` | None, Read, Edit | Specify no value if contacts are Public Read/Write or Controlled By Parent | _____________ |
| `caseAccessLevel` | None, Read, Edit | Specify no value if cases/opportunities are Public Read/Write | _____________ |

Org-level defaults in `Territory2.settings`: `defaultAccountAccessLevel` _______, `defaultOpportunityAccessLevel` _______, `defaultContactAccessLevel` _______, `defaultCaseAccessLevel` _______, `t2ForecastAccessLevel` (View / Edit) _______

`Territory2ObjSharingConfig` is a query/update-only SOAP object for the objects enabled through `Territory2Settings.supportedObjects` — documented today as `Lead` only. There is nothing to deploy here. Leads in scope? Yes / No: _______

---

## 7. Forecast Configuration

Complete this section if territory-based forecasting is required.

| Field | Value |
|---|---|
| Forecast Type Name | _____________ |
| Forecast Hierarchy Source | Territory Model: _____________ |
| Forecast Measure | _____________ (e.g., Amount, CloseDate) |
| Forecast Manager (root) | _____________ |
| Forecast Users (territory managers) | _____________ |
| Sharing supported? | No — territory forecast types do not support forecast sharing |
| Opportunity territory assignment mechanism | Apex filter (`Territory2Settings.opportunityFilterSettings`) / manual `Territory2Id` / none |
| Apex class implementing `TerritoryMgmt.OpportunityTerritory2AssignmentFilter` | _____________ (`enableFilter` _______, `runOnCreate` _______, `runMultiThreaded` _______) |

---

## 8. Deployment Checklist

- [ ] `Territory2.settings` deployed FIRST, on its own (`enableTerritoryManagement2` is exclusive of all other operations)
- [ ] Territory model source reviewed in sandbox (`Territory2Model`, `Territory2Type`, `Territory2`, `Territory2Rule`)
- [ ] `python3 scripts/check_enterprise_territory_management.py --manifest-dir <dir>` reports no ERROR findings
- [ ] Manifest members are model-qualified for `Territory2` and `Territory2Rule` (`Model.Component`), plain for `Territory2Type`
- [ ] Target org confirmed to have no same-named model in `Archived` state
- [ ] Assignment rules run in preview mode against sandbox data — results validated
- [ ] UserTerritory2Association records confirmed for all reps and managers (insert before delete during realignment)
- [ ] Per-territory access levels reviewed and approved, in Metadata API spelling
- [ ] Activation window scheduled and communicated to sales operations
- [ ] Monitoring plan in place: Territory2AlignmentLog queried after activation to confirm completion
- [ ] Forecast Type configured and forecast users enabled (if territory forecast is used)
- [ ] Rollback plan documented: if activation produces unexpected results, what is the contingency?

---

## 9. Post-Activation Verification Queries

Run these SOQL queries after activation to confirm the model is correctly deployed.

```sql
-- Confirm exactly one active model, and that nothing is stuck mid-transition.
-- Full State picklist: Planning, Activating, Activation Failed, Active,
-- Archiving, Archiving Failed, Archived, Deleting, Deletion Failed.
SELECT Id, DeveloperName, State, ActivatedDate, LastRunRulesEndDate, LastOppTerrAssignEndDate
FROM Territory2Model
WHERE State != 'Archived'

-- Count territories in the active model
SELECT COUNT() FROM Territory2 WHERE Territory2Model.State = 'Active'

-- Check the alignment log for completion. Territory2Id is null for a model-level run;
-- there is no LastRunDate field on this object.
SELECT Id, Territory2ModelId, Territory2Id, Status, StartTime, EndTime, RunAsId
FROM Territory2AlignmentLog
ORDER BY StartTime DESC
LIMIT 50

-- Find accounts with no territory assignment
SELECT Id, Name, BillingCountry FROM Account
WHERE Id NOT IN (SELECT ObjectId FROM ObjectTerritory2Association WHERE SobjectType = 'Account')
LIMIT 100

-- Find open opps with no territory (forecast gap)
SELECT Id, Name, AccountId, CloseDate FROM Opportunity
WHERE Territory2Id = null AND IsClosed = false
LIMIT 100

-- Prove the share rows exist. Territory = granted by an assignment rule;
-- Territory2AssociationManual = granted by a manual account-to-territory assignment.
SELECT UserOrGroupId, AccountAccessLevel, OpportunityAccessLevel, CaseAccessLevel, RowCause
FROM AccountShare
WHERE AccountId = 'REPLACE_ME'
  AND RowCause IN ('Territory', 'Territory2AssociationManual')
```

---

## 10. Notes and Decisions

Record any deviations from the standard approach, stakeholder decisions, or known limitations.

| Decision | Rationale | Owner | Date |
|---|---|---|---|
| _____________ | _____________ | _____________ | _____________ |
| _____________ | _____________ | _____________ | _____________ |
