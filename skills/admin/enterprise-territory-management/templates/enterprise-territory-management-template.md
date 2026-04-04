# Enterprise Territory Management — Territory Model Design Template

Use this template when designing a new territory model or documenting an existing one for review or deployment.

---

## 1. Model Overview

| Field | Value |
|---|---|
| Territory Model Name | _____________ |
| Model Label (API) | _____________ |
| Model Purpose | _____________ (e.g., "FY26 North America field sales and named account coverage") |
| Target Activation Date | _____________ |
| Activation Window | _____________ (e.g., "Saturday 10 PM–12 AM PST") |
| Current State | Planning / Active / Archived |

---

## 2. Territory Types

Define at least one territory type before creating territories. Lower priority integer = higher precedence for opportunity territory assignment (OTA) tie-breaking.

| Territory Type Name | API Name | Priority Value | Description / Use Case |
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

Total territory count: _____ (must be below 1,000 for Enterprise Edition; request increase from Salesforce Support for Performance/Unlimited)

---

## 4. Account Assignment Rules

For each territory, document the filter criteria that will drive automatic account assignment.

| Territory Name | Rule Name | Field | Operator | Value(s) | Auto-Run (IsActive)? |
|---|---|---|---|---|---|
| _____________ | _____________ | BillingState | EQUALS | _____________ | Yes / No |
| _____________ | _____________ | Industry | EQUALS | _____________ | Yes / No |
| _____________ | _____________ | _____________ | _____________ | _____________ | Yes / No |
| _____________ | _____________ | _____________ | _____________ | _____________ | Yes / No |

Notes on rule design:
- If an account matches rules for multiple territories, it will be assigned to ALL matching territories. Confirm this is intentional.
- Rules are not retroactive. After creating or modifying rules, manually run assignment at the model level to apply to existing accounts.
- Test rule coverage in preview mode before activation.

---

## 5. User Territory Memberships

List users and their territory assignments. Users can be members of multiple territories.

| User Name | Territory Name | Territory Role | Notes |
|---|---|---|---|
| _____________ | _____________ | _____________ (e.g., Account Executive) | _____________ |
| _____________ | _____________ | Territory Manager | Forecast user; manages sub-territory rollup |
| _____________ | _____________ | _____________ | _____________ |

---

## 6. Object Sharing Configuration (Territory2ObjSharingConfig)

Define the access level territory members receive for related objects.

| Object | Access Level for Territory Members | Notes |
|---|---|---|
| Account | Read (minimum; always granted) | Cannot be reduced below Read |
| Opportunity | Read / Read-Write | _____________ |
| Contact | Read / Read-Write | _____________ |
| Case | Read / Read-Write | _____________ |

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

---

## 8. Deployment Checklist

- [ ] Territory model metadata reviewed in sandbox (Territory2Model, Territory2Type, Territory2, AccountTerritoryAssignmentRule)
- [ ] Assignment rules run in preview mode against sandbox data — results validated
- [ ] UserTerritory2Association records confirmed for all reps and managers
- [ ] Territory2ObjSharingConfig access levels reviewed and approved
- [ ] Activation window scheduled and communicated to sales operations
- [ ] Monitoring plan in place: Territory2AlignmentLog queried after activation to confirm completion
- [ ] Forecast Type configured and forecast users enabled (if territory forecast is used)
- [ ] Rollback plan documented: if activation produces unexpected results, what is the contingency?

---

## 9. Post-Activation Verification Queries

Run these SOQL queries after activation to confirm the model is correctly deployed.

```sql
-- Confirm exactly one active model
SELECT Id, Name, State FROM Territory2Model WHERE State = 'Active'

-- Count territories in the active model
SELECT COUNT() FROM Territory2 WHERE Territory2Model.State = 'Active'

-- Check alignment log for completion
SELECT Territory2Id, LastRunDate, Status FROM Territory2AlignmentLog ORDER BY LastRunDate DESC LIMIT 50

-- Find accounts with no territory assignment
SELECT Id, Name, BillingState FROM Account
WHERE Id NOT IN (SELECT AccountId FROM ObjectTerritory2Association)
LIMIT 100

-- Find open opps with no territory (forecast gap)
SELECT Id, Name, AccountId, CloseDate FROM Opportunity
WHERE Territory2Id = null AND IsClosed = false
LIMIT 100
```

---

## 10. Notes and Decisions

Record any deviations from the standard approach, stakeholder decisions, or known limitations.

| Decision | Rationale | Owner | Date |
|---|---|---|---|
| _____________ | _____________ | _____________ | _____________ |
| _____________ | _____________ | _____________ | _____________ |
