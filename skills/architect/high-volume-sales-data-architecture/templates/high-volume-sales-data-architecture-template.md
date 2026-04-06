# High Volume Sales Data Architecture -- Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `high-volume-sales-data-architecture`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Record counts:** Account: ___ / Opportunity: ___ / OpportunityLineItem: ___ / Monthly growth rate: ___
- **Ownership distribution:** Highest single-owner Account count: ___ / User or queue: ___ / Integration user record count: ___
- **Report performance:** Slowest report name: ___ / Filter fields used: ___ / Indexed? Y/N / Estimated result set size: ___
- **Retention policy:** Archival cutoff (e.g., ClosedDate > 2 years): ___ / Compliance requirements: ___

## Skew Analysis

| Object | Owner | Record Count | Above 10K Threshold? | Action |
|--------|-------|-------------|----------------------|--------|
| Account | ___ | ___ | Y/N | ___ |
| Opportunity | ___ | ___ | Y/N | ___ |

## Index and Skinny Table Assessment

| Object | Field | Currently Indexed? | Selectivity (filter count / total) | Action Needed |
|--------|-------|-------------------|-----------------------------------|---------------|
| ___ | ___ | Y/N | ___% | Request index / Already selective / Not needed |

## Archival Design

- **Archival criteria:** ___
- **Big Object name:** ___
- **Composite index fields:** ___
- **Summary custom object needed?** Y/N
- **Estimated records to archive:** ___
- **Hard-delete after verification?** Y/N

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Pattern 1: Ownership Redistribution -- because ___
- [ ] Pattern 2: Tiered Archival with Big Objects -- because ___
- [ ] Pattern 3: Custom Index and Skinny Table Requests -- because ___

## Review Checklist

Copy from SKILL.md and tick items as you complete them.

- [ ] No single user owns more than 10,000 Accounts or Opportunities
- [ ] All high-volume SOQL queries use selective WHERE clauses against indexed fields
- [ ] Pipeline and forecast reports include date-range filters that keep result sets under 2,000 detail rows
- [ ] Archival Big Object schema is defined with appropriate composite index
- [ ] Archival batch job has been tested with production-scale data in sandbox
- [ ] Skinny table and custom index requests have been filed with Salesforce Support where needed
- [ ] Sharing rule recalculation duration is within acceptable SLA after ownership redistribution

## Notes

Record any deviations from the standard pattern and why.
