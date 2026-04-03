# Well-Architected Notes — Custom Field Creation

## Relevant Pillars

- **Security** — Field-Level Security is the primary Salesforce mechanism for controlling who reads and edits specific data at the field granularity. Every custom field must have an explicit FLS design: which profiles or permission sets get Read, which get Edit, and which should have no access. Skipping FLS configuration is not a neutral default — it means all users with "View All Data" or Administrator access can read the field via API even if it is not visible in the UI. Security must be intentional, not accidental.

- **Operational Excellence** — Field type decisions made at creation time cannot be undone for most types. Choosing the wrong type (Text instead of Picklist, Lookup instead of Master-Detail) creates technical debt that is expensive to correct: new field creation, data migration, update of all references in flows/apex/reports, and removal of the old field. Operational Excellence here means making deliberate, documented decisions at creation time rather than improvising and correcting later.

- **Scalability** — Custom field count per object is a hard platform limit (500 in Enterprise, 800 in Unlimited/Performance). Orgs with many custom objects and fields across hundreds of integrations approach this limit. Adding a field for every one-off reporting request without a field governance process creates objects with hundreds of fields, many of which become unused over time. Field creation should be intentional and subject to a governance review for large orgs.

## Architectural Tradeoffs

**Field type vs flexibility:** Text fields are maximally flexible but provide no validation by construction. Picklist fields enforce a controlled vocabulary but require admin intervention to add values. For data that must be filterable, reportable, and consistent, Picklist is almost always correct for enumerated values. Text is correct only for genuinely free-form data.

**Required at field level vs Required on page layout vs Validation Rule:** There are three distinct ways to require a field in Salesforce:
1. **Required at field definition** — enforced by the API on all DML. Strongest, least flexible. Breaks integrations that don't send the field.
2. **Required on page layout** — enforced only in the UI for users using that layout. API and integrations bypass it. Weakest.
3. **Validation rule** — enforced by the API but configurable with bypass conditions (Custom Permission, Profile check, RecordType). Most flexible. Recommended for orgs with integrations or data migration needs.

**Lookup vs Master-Detail:** Lookup is the safe default when the relationship semantics are not yet clear. Master-Detail commits to cascade delete behavior and roll-up summary support. Converting from Lookup to Master-Detail later is possible but requires all child records to have a non-null parent. Converting from Master-Detail to Lookup requires removing any Roll-Up Summary fields first.

## Anti-Patterns

1. **Creating a field first, configuring FLS and layouts later** — In practice, "later" often means never, or it means the field is visible to the wrong users for weeks after creation. Configure FLS and page layouts during the same deployment as the field. The field, its FLS, and the page layout updates should be in the same change set or SFDX deploy.

2. **Using Text fields for enumerated categorical data** — Text fields for categories that belong in a Picklist produce messy data: typos, inconsistent capitalization, and brittle report filters. Every Text field used for categorical data eventually requires a validation rule to maintain data quality — a validation rule that reimplements what a Picklist provides by default.

3. **Treating a field as harmless if not on a page layout** — A field not on any page layout is still readable and writeable via the REST API and SOQL by any user with FLS Read access. If a field should not be accessed programmatically by certain integrations or users, FLS must be configured — hiding the field from page layouts is insufficient security.

## Official Sources Used

- Salesforce Help — Custom Field Types: https://help.salesforce.com/s/articleView?id=sf.custom_field_types.htm
- Salesforce Help — Custom Field Allocations (limits by edition): https://help.salesforce.com/s/articleView?id=platform.custom_field_allocations.htm
- Object Reference — sObject field concepts: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — CustomField metadata type: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help — Field-Level Security Overview: https://help.salesforce.com/s/articleView?id=sf.admin_fls.htm
