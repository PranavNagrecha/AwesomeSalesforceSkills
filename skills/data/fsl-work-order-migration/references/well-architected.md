# Well-Architected Notes — FSL Work Order Migration

## Relevant Pillars

- **Reliability** — FSL's object hierarchy has strict insert-order dependencies. A single failed step invalidates all subsequent loads. Use External IDs and upsert operations to make every step re-runnable. Validate zero errors at each hierarchical level before proceeding.
- **Performance** — FSL scheduling automation fires on AssignedResource inserts. Bulk loading without disabling optimization creates a compounding background job queue that can extend migration windows from hours to days. Disable optimization settings before migration.
- **Security** — Migration users require FSL object-level permissions and Field Service license assignments. Running migrations as System Administrator is acceptable for migration batches but production loads should use a dedicated integration user with scoped permissions.

## Architectural Tradeoffs

**Upsert vs. Insert:** Upsert with External IDs adds field configuration overhead but enables safe re-runs. For one-time historical loads, some teams use insert-only for speed. The risk is that any partial failure requires a full delete-and-reload, which is significantly slower. Recommendation: always use upsert for FSL migrations.

**Full history vs. open records only:** Migrating historical completed appointments significantly increases complexity (status picklist activation, ProductConsumed pre-requisites, scheduling automation handling). If business requirements only need open/scheduled records, scope the migration to non-completed appointments to reduce risk.

**Batch size:** Use smaller batch sizes (50-100 records) for ServiceAppointment and AssignedResource loads to reduce the impact of individual record failures. Data Loader's default of 200 can amplify failures in FSL loads where related automation is sensitive to transaction size.

## Anti-Patterns

1. **Loading FSL objects without disabling scheduling automation** — AssignedResource and ServiceAppointment inserts trigger scheduling engine jobs that conflict with migration-set scheduled times and dramatically slow the load process.
2. **Migrating Case data and Work Order data together in a single batch** — WorkOrders may reference Cases, but these are separate object hierarchies with different dependencies. Mix loading them causes lookup failures when Cases aren't present yet.
3. **Skipping External IDs for FSL objects** — Without External IDs, any partial failure requires identifying and deleting duplicates before re-running. This is especially painful for AssignedResource records where direct SOQL querying requires knowing the parent ServiceAppointment IDs.

## Official Sources Used

- WorkOrder Object (Field Service Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/apex_namespace_fsl_workorder.htm
- AssignedResource Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_assignedresource.htm
- ProductConsumed Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_productconsumed.htm
- Guidelines for Creating Work Orders (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.fs_work_orders_guidelines.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
