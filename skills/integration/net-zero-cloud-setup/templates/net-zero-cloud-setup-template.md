# Net Zero Cloud Setup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `net-zero-cloud-setup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Net Zero Cloud license confirmed active (standard objects visible): YES / NO
- Disclosure framework(s) in scope (CSRD/ESRS, TCFD, CDP, SBTi, GHG Protocol):
- Operating regions (drives factor set selection):
- Activity data sources (utility bills, fuel logs, ERP spend, supplier data):
- Inventory boundary (operational control / equity share / financial control):
- Base year:

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Initial carbon inventory setup
- [ ] Pattern 2: Refreshing historical totals after factor update
- [ ] Pattern 3: Supplier engagement for purchased goods

## Checklist

- [ ] Disclosure framework(s) identified before object loading
- [ ] `EmssnFctrSet` activated for all operating regions
- [ ] Stationary asset records have activity rows for all fuel / electricity types
- [ ] Vehicle asset records distinct from any Automotive Cloud `Vehicle` records
- [ ] Scope 3 categories loaded only for material categories (not all 15 by default)
- [ ] Carbon calculation DPE definitions activated AND scheduled
- [ ] First calculation manually executed; `…CrbnFtprnt` rows populated
- [ ] Disclosure pack(s) configured per framework (one pack per framework)
- [ ] Audit-log entries for inventory boundary, base year, and factor sets used
- [ ] Custom factor sets justified by auditor / regulator requirement (not preference)

## Notes

Record any deviations from the standard pattern and why.
