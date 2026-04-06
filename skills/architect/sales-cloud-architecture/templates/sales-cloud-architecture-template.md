# Sales Cloud Architecture — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `sales-cloud-architecture`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Edition and licenses:** (e.g., Enterprise Edition, Sales Cloud, Territory Management licensed)
- **User count:** (number of sales reps, managers, admins)
- **Record volumes:** (leads/month, opportunities/quarter, activities/user/day)
- **Existing automation inventory:** (count of Flows, Process Builders, Apex triggers, Workflow Rules per object)
- **Integration landscape:** (list of external systems — ERP, marketing, CPQ, commission)
- **Known constraints:** (multi-currency, Person Accounts, sandbox availability)

## Data Model Assessment

| Object | Record Type(s) | Custom Field Count | Automation Count | Volume Estimate |
|---|---|---|---|---|
| Lead | | | | /month |
| Account | | | | total |
| Contact | | | | total |
| Opportunity | | | | /quarter |
| (custom) | | | | |

## Automation Ownership Map

| Object | Before-Save | After-Save | Async | Scheduled |
|---|---|---|---|---|
| Lead | | | | |
| Account | | | | |
| Contact | | | | |
| Opportunity | | | | |

## Integration Boundary Inventory

| External System | Direction | Pattern | System of Record | Error Strategy |
|---|---|---|---|---|
| | | | | |

## Scalability Analysis

| Transaction Profile | SOQL Queries | DML Statements | Heap (est.) | Headroom |
|---|---|---|---|---|
| Single Opportunity save | | | | |
| Bulk lead conversion (200) | | | | |
| Territory reassignment batch | | | | |

## Architecture Decisions

### Decision 1: (title)

- **Options considered:**
- **Chosen approach:**
- **Rationale:**
- **Tradeoffs:**

### Decision 2: (title)

- **Options considered:**
- **Chosen approach:**
- **Rationale:**
- **Tradeoffs:**

## Review Checklist

Copy from SKILL.md and tick items as you complete them.

- [ ] Data model uses standard Sales Cloud objects where they exist; custom objects are justified
- [ ] Each object has at most one automation owner per timing slot
- [ ] No synchronous callouts from Opportunity or Lead triggers without Platform Event decoupling
- [ ] Governor limit analysis exists for all critical transaction profiles with 50% headroom
- [ ] Territory Management approach is documented with assignment rules
- [ ] Integration boundaries define system of record, field mapping, and error handling per system
- [ ] Forecasting configuration aligns with fiscal year and territory hierarchy
- [ ] Sharing model is validated — OWD settings, sharing rules, and territory sharing are coherent
- [ ] Historical reporting strategy does not rely on live queries against multi-million-row objects

## Notes

Record any deviations from the standard pattern and why.
