# Well-Architected Notes — Object Creation and Design

## Relevant Pillars

- **Security** — The OWD chosen at object creation is the security floor for all records on that object. Choosing Public Read/Write when records contain sensitive or personally identifiable data violates the principle of least privilege. The correct pattern is to start with the most restrictive OWD and open access upward through sharing rules and role hierarchy — not to start open and try to restrict.

- **Scalability** — Object creation decisions have long-running scalability implications. Enabling Track Field History on a high-volume object generates History rows at a rate of (tracked fields × DML writes per day). Over three to five years in a large org, this compounds into tens of millions of History rows that slow related list queries and consume storage. Similarly, a Public Read/Write or Public Read Only OWD generates more sharing-related processing overhead than Private on high-record-count objects.

- **Operational Excellence** — Every permanent choice made at object creation (API name, Record Name type, enabled features) becomes a maintenance burden if chosen carelessly. A clear, permanent API name reduces onboarding friction for new developers. A well-written object Description helps future admins understand the purpose without reading the data model documentation separately.

## Architectural Tradeoffs

**OWD Private vs. Public Read Only:**
Private gives the tightest security floor and the least sharing overhead but requires explicit sharing rules for cross-owner access. Public Read Only removes the need for read-access sharing rules but grants all internal users read access by default — including users in different business units or regions who may not have a business need to see those records.

Choose Private when: the object contains sensitive data, different business units should not see each other's records by default, or the org has a complex role hierarchy with deliberate access segmentation.

Choose Public Read Only when: the object is essentially a shared reference or workflow artifact (e.g. project requests, service requests) where visibility to all users is acceptable but edit access needs control.

**Auto Number vs. Text Record Name:**
Auto Number Record Names eliminate data quality issues with name fields (blanks, duplicates, inconsistent formats) at the cost of a less human-meaningful primary display label. Use Auto Number for transactional records (cases, requests, inspections, work orders) where a stable, unique reference ID matters. Use Text when the record name is a natural business identifier that users know and enter reliably (e.g. contract numbers that come from a contract management system as external IDs).

**Controlled by Parent vs. Private OWD:**
Controlled by Parent ties child record access entirely to parent access — it is simpler to reason about but removes the ability to create sharing rules or manual shares directly on the child object. Use it only when child records should always and exclusively be accessible through their parent, and when no use case exists for sharing a child record independently of its parent.

## Anti-Patterns

1. **Enabling all optional features at object creation "for safety"** — Activities, Track Field History, and Chatter cannot be disabled once enabled. Enabling them on objects where they will not be used wastes storage, adds framework overhead, and permanently increases the object's maintenance surface. Enable only what has a confirmed current use case.

2. **Setting OWD to Public Read/Write as the default "to make things simple"** — A permissive OWD cannot be restricted later without a disruptive recalculation. Starting with Private and opening access through sharing rules is operationally safe. Starting with Public Read/Write and then discovering that records contain sensitive data requires an emergency OWD change and a potential compliance incident investigation.

3. **Not reviewing the API name before saving** — The object API name is permanent. An unclear, abbreviated, or project-codename API name (e.g. `CS_Plan__c` for "Customer Success Plan") degrades developer experience for the lifetime of the org. Treat the API name review as a mandatory gate before saving.

## Official Sources Used

- Salesforce Help — Create a Custom Object in Lightning Experience: https://help.salesforce.com/s/articleView?id=platform.dev_objectcreate_task_lex.htm
- Salesforce Help — Considerations for Creating Custom Objects: https://help.salesforce.com/s/articleView?id=platform.dev_objectcreate_notes.htm
- Salesforce Help — Set Your Internal Organization-Wide Sharing Defaults: https://help.salesforce.com/s/articleView?id=platform.admin_sharing.htm
- Salesforce Help — Enterprise Edition Allocations (custom object limits): https://help.salesforce.com/s/articleView?id=xcloud.overview_limits_enterprise.htm
- Salesforce Help — Create a Custom Object Tab: https://help.salesforce.com/s/articleView?id=platform.creating_custom_object_tabs.htm
- Object Reference — Custom Objects: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_custom_objects.htm
- Salesforce Features and Edition Allocations (limits cheatsheet): https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_features.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
