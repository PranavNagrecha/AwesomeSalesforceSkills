# NPSP Custom Rollups (CRLP) — Work Template

Use this template when configuring, troubleshooting, or extending NPSP Customizable Rollups.

---

## Scope

**Skill:** `npsp-custom-rollups`

**Request summary:** (describe what the user asked for — e.g., "create a fiscal year gift rollup", "fix stale totals after data load", "migrate from legacy NPSP rollups")

---

## Context Gathered

Answer these before starting any configuration work:

- **CRLP enabled?** Yes / No / Unknown (check NPSP Settings > Customizable Rollups)
- **NPSP version:** _____________ (check Setup > Installed Packages)
- **Legacy rollup fields in active use:** List fields or write "not applicable if CRLP already enabled"
- **Downstream dependencies on rollup fields:** Formula fields / flows / Apex / reports that read rollup fields
- **Business rule for date range:** Calendar year / Fiscal year / Custom window
- **Bulk data load pending or recently completed?** Yes / No (if yes, Full recalculation is required)

---

## Rollup Definition Plan

Complete one row per rollup needed:

| Rollup Name | Summary Object | Detail Object | Aggregate Operation | Amount/Date Field | Date Range Type | Store Field | Filter Group |
|---|---|---|---|---|---|---|---|
| (e.g., Contact FY Total Giving) | Contact | Opportunity | Sum | Amount | Current Fiscal Year | npo02__TotalOppAmount__c | (name, max 40 chars) |
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |

---

## Filter Group Plan

Complete one block per filter group needed:

**Filter Group Name:** _________________________ (must be 40 characters or fewer — count: ___ chars)

| Row | Object | Field | Operator | Value | AND/OR |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |

---

## Pre-Migration Checklist (complete only if enabling CRLP for the first time)

- [ ] Legacy rollup fields exported from NPSP Rollups tab
- [ ] Formula fields referencing legacy rollup fields identified: _______________
- [ ] Flows referencing legacy rollup fields identified: _______________
- [ ] Apex classes referencing legacy rollup fields identified: _______________
- [ ] Validation rules referencing legacy rollup fields identified: _______________
- [ ] Equivalent CRLP Rollup Definitions created or documented as gaps before enabling CRLP

---

## Deployment Approach

- [ ] Building in sandbox first (recommended)
- [ ] Deploying via Metadata API (recommended for production promotion)
- [ ] Manual UI configuration only (acceptable for initial sandbox exploration)

**Metadata types to retrieve/deploy:**
- `CustomMetadata:Customizable_Rollup__mdt`
- `CustomMetadata:Customizable_Rollup_Filter_Group__mdt`
- `CustomMetadata:Customizable_Rollup_Filter_Rules__mdt`

---

## Post-Configuration Checklist

- [ ] All Rollup Definitions saved without errors
- [ ] All filter group names confirmed at 40 characters or fewer
- [ ] Full recalculation batch triggered (NPSP Settings > Batch Processing > Recalculate Rollups > Full)
- [ ] Full recalculation batch completed without errors
- [ ] Rollup values verified on 5+ sample Contact records against expected figures
- [ ] Rollup values verified on 5+ sample Account records (if Account rollups configured)
- [ ] Downstream formula fields / flows re-validated post-configuration
- [ ] Scheduled Incremental recalculation configured for ongoing operation

---

## Notes

(Record deviations from the standard pattern, unresolved questions, or decisions made during this work.)
