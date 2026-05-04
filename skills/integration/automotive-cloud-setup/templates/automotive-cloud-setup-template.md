# Automotive Cloud Setup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `automotive-cloud-setup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Automotive Cloud license confirmed active (standard objects visible in Object Manager): YES / NO
- Source-of-truth for VIN data (DMS / OEM feed / Salesforce-as-SoR):
- Dealer org structure (single-tenant / multi-dealer / multi-franchise):
- Lifecycle events in scope (recall / service / warranty / financial):

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: VIN ingestion with definition deduplication
- [ ] Pattern 2: Multi-franchise dealer hierarchy via AccountAccountRelation
- [ ] Pattern 3: Recall / service campaign orchestration via ActionableEvent

## Checklist

- [ ] `VehicleDefinition` and `Vehicle` correctly separated — pricing / specs not duplicated per VIN
- [ ] External IDs on both Vehicle and VehicleDefinition for idempotent reload
- [ ] `AccountAccountRelation` used for OEM-Dealer relationships (not `ParentId`)
- [ ] Sharing rules reference `AccountAccountRelation`, not `ParentId`
- [ ] `ActionableEventType` + `ActionableEventTypeDef` defined before generating orchestrations
- [ ] FinancialAccount records linked to both Vehicle and Opportunity (no orphan financials)
- [ ] DriverQualification only populated for fleet-customer scenarios (not retail)
- [ ] `Appraisal` standard object used rather than a custom `Appraisal__c`
- [ ] `VehDefSearchableField` rows populated for each searchable spec attribute

## Notes

Record any deviations from the standard pattern and why.
