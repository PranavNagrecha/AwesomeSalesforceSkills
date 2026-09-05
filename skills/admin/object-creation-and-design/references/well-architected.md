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

**Owner-less detail objects vs. an independent child:**
A master-detail relationship buys cascade delete, roll-up summary fields and inherited security, and it costs the child object its Owner field — and with it every mechanism that depends on ownership: sharing rules, manual shares, queues, and therefore assignment rules and Omni-Channel routing (object_reference.txt L3259–3261). The trade is not "tighter security vs. looser security"; it is "security that follows the parent" vs. "the ability to route, reassign and share the child on its own terms". Under **Security** the master-detail option is usually the stronger default, because access is derived from one place instead of maintained in two. Under **Operational Excellence** it is the weaker one whenever the child is a work item that someone must be assigned. Decide which of those the object actually is before the relationship is created, because converting master-detail to lookup afterwards rewrites the object's whole access footprint.

## Official Sources Used

- Metadata API Developer Guide (v62 PDF), `CustomObject` type — field table and Declarative Metadata Sample Definition: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (element names, `deploymentStatus`, `sharingModel`, `externalSharingModel`, `nameField`, the `enableBulkApi`/`enableSharing`/`enableStreamingApi` dependency, `enableSearch` defaults and the 120-day searchability rule, `visibility`, wildcard support — Core Concepts §2, `references/metadata-examples.md`, gotchas #7, #8, #10)
- Metadata API Developer Guide (v62 PDF), `CustomField` type: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`displayFormat`, the non-retrievable `startingNumber`, `trackHistory` requiring `enableHistory`, `relationshipOrder`, `reparentableMasterDetail`, `writeRequiresMasterRead` — `references/metadata-examples.md`, gotchas #6)
- Metadata API Developer Guide (v62 PDF), `CustomTab` type: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`customObject`, `motif`, `frameHeight`, the mutually exclusive content elements, and the note that retrieving a tab rewrites Profile and PermissionSet components in the same package — Pattern 3, gotchas #10)
- Metadata API Developer Guide (v62 PDF), `HistoryRetentionPolicy` and `Metadata Field Types` (`SharingModel`, `DeploymentStatus`): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the valid OWD enum values including `ControlledByParent`, the `InDevelopment`/`Deployed` pair, and the Field Audit Trail `RetainFieldHistory` requirement behind history retention — Core Concepts §2 and §3, gotchas #11)
- Object Reference (v62 PDF), "Custom Objects" and "Relationships Among Standard Objects and Fields": https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the detail object having no Owner field and therefore no sharing rules, manual sharing or queues; the standard objects that cannot be the master; API-created records without a name taking their record ID as their name — Architectural Tradeoffs above, gotchas #5, #9)
- Object Reference (v62 PDF), `EntityHistory` usage notes and the object-suffix table: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the twenty-field tracking ceiling, that turning tracking off does not delete history while deleting the field does, and the `__History` suffix used in the verification query — gotchas #11, `references/metadata-examples.md`)
- Salesforce Help — Create a Custom Object in Lightning Experience: https://help.salesforce.com/s/articleView?id=platform.dev_objectcreate_task_lex.htm
- Salesforce Help — Considerations for Creating Custom Objects: https://help.salesforce.com/s/articleView?id=platform.dev_objectcreate_notes.htm
- Salesforce Help — Set Your Internal Organization-Wide Sharing Defaults: https://help.salesforce.com/s/articleView?id=platform.admin_sharing.htm
- Salesforce Help — Enterprise Edition Allocations (custom object limits): https://help.salesforce.com/s/articleView?id=xcloud.overview_limits_enterprise.htm
- Salesforce Help — Create a Custom Object Tab: https://help.salesforce.com/s/articleView?id=platform.creating_custom_object_tabs.htm
- Object Reference — Custom Objects: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_custom_objects.htm
- Salesforce Features and Edition Allocations (limits cheatsheet): https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_features.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
