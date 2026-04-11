# Well-Architected Notes — NPSP Data Model

## Relevant Pillars

- **Reliability** — The most critical pillar for NPSP data model work. Incorrect namespace prefixes cause silent query failures; improper Opportunity deletion leaves orphaned allocation records; missing parent recurring donation references corrupt rollup fields. Reliable NPSP implementations require rigorous use of the correct API names and explicit handling of lookup-based relationships that do not cascade.
- **Operational Excellence** — NPSP's multi-namespace structure requires documented conventions and automated checks to prevent namespace drift across a team. Checker scripts and linting patterns (see `scripts/check_npsp_data_model.py`) are essential for maintaining correctness at scale.
- **Security** — NPSP objects (especially `npsp__General_Accounting_Unit__c` and `npsp__Allocation__c`) may hold financial data subject to organizational access controls. Field-level security and object-level permissions must be explicitly configured for each namespace's objects; the managed package installer grants access to admins but not necessarily to all profiles.
- **Performance** — Queries against large NPSP orgs (high donation volume nonprofits) can be slow if SOQL is not selective. `npsp__Allocation__c` and `npe03__Recurring_Donation__c` tables can grow large; always filter by indexed fields like `npsp__Opportunity__c` or `npe03__Contact__c`.
- **Scalability** — NPSP's trigger framework (`npsp__Trigger_Handler__c`) processes donations, payments, allocations, and rollups synchronously. High-volume donation imports (e.g., end-of-year giving campaigns) can hit governor limits if not batched correctly. NPSP-provided batch classes should be used instead of custom Apex for bulk recalculation of rollups.

## Architectural Tradeoffs

**Lookup vs. Master-Detail for GAU Allocations:** The `npsp__Allocation__c` object uses a lookup to `Opportunity` rather than a master-detail relationship. This was a deliberate design choice to allow allocations to exist independently and be reassigned. The tradeoff is that cascade delete is not available, requiring explicit allocation management in all delete and migration workflows. Orgs that need enforced referential integrity on allocations should implement a before-delete trigger on Opportunity to either delete or reassign allocations.

**Multi-Namespace Package Architecture:** NPSP's five-namespace structure reflects the history of how NPSP was assembled from separately developed packages (Households, Recurring Donations, Relationships, Affiliations, Core). This architecture means the data model cannot be fully described by a single namespace or a single object reference document. Teams working with NPSP data must maintain the full namespace mapping and cannot rely on convention to infer correct API names.

**Rollup Fields vs. Custom Reporting:** NPSP maintains rollup fields on Contact and Account through its own trigger-based rollup engine (not standard Roll-Up Summary fields, which are master-detail only). These rollups are powerful but require the parent-child relationships to be intact. For complex reporting that needs real-time accuracy without the rollup lag, direct SOQL against `npsp__Allocation__c` and `npe03__Recurring_Donation__c` is more reliable than reading stale rollup values.

## Anti-Patterns

1. **Uniform npsp__ namespace assumption** — Treating all NPSP objects as if they share the `npsp__` namespace causes half of all NPSP object references to be silently wrong. Payment objects, recurring donation objects, relationships, and affiliations each use a different prefix. This anti-pattern is particularly dangerous because it produces no runtime errors in SOQL, only wrong data.

2. **Bulk Opportunity delete without allocation cleanup** — Deleting Opportunities in a data cleanup script without first removing or reassigning their `npsp__Allocation__c` records leaves orphaned financial data in the org. GAU reports will show inflated totals, and the orphaned records cannot be easily discovered through standard reporting because their parent Opportunity no longer exists.

3. **Direct installment Opportunity creation bypassing the recurring donation parent** — Creating installment Opportunities as standalone records (without populating the `npe03__Recurring_Donation__c` lookup) breaks NPSP's schedule tracking and rollup engine. This produces incorrect "total given" values on Contact and Account records and causes the recurring donation's own status and amount tracking to diverge from actual giving history.

## Official Sources Used

- NPSP Data Model Gallery — https://developer.salesforce.com/docs/nonprofit/npsp/guide/npsp-data-model.html
- NPSP Objects and Fields Data Dictionary — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Objects_and_Fields_Data_Dictionary.htm&type=5
- Trailhead: Explore the NPSP Data Model — https://trailhead.salesforce.com/content/learn/modules/nonprofit-success-pack-basics/explore-the-npsp-data-model
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
- Object Reference (standard objects referenced by NPSP) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
