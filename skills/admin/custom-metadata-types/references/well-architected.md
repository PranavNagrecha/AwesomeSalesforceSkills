# Well-Architected Notes - Custom Metadata Types

## Relevant Pillars

### Operational Excellence

Custom Metadata Types improve operational consistency because configuration can move through source control, code review, deployment automation, and rollback paths instead of living only in manual production edits.

### Reliability

Metadata-driven configuration reduces environment drift and hardcoded IDs. The same release artifact can promote rules and defaults consistently across sandboxes and production.

### Security

Security matters because teams often misuse CMT for secrets or misunderstand protected visibility. The right design keeps credentials in Named Credentials and uses packaging visibility intentionally.

## Architectural Tradeoffs

- **Deployable control vs rapid production edits:** CMT is safer for release-managed config, but it is intentionally less convenient for ad hoc operational editing.
- **Public subscriber flexibility vs protected package defaults:** Public records are easier for admins to adjust, while protected defaults preserve package-owned internals.
- **One shared config store vs clear separation of concerns:** It is tempting to put every value in CMT, but user overrides, secrets, and reportable data often belong elsewhere.

## Anti-Patterns

1. **Secrets in public custom metadata** - configuration becomes readable in places where credentials should never live.
2. **Treating metadata as transactional data** - operations workflows become awkward because the storage model fights the runtime behavior.
3. **Hardcoded org-specific IDs alongside CMT** - the team pays the complexity cost of metadata without actually removing deployment drift.

## Official Sources Used

- Metadata API Developer Guide — *Custom Metadata Types (CustomObject)*, pp. 745–747 (the `__mdt` suffix and `objects` folder location, the `visibility` enum `Public` / `Protected` / `PackageProtected`, the "Author Apex" permission, the 1,000-character `description` limit, and the sample type definition reproduced in `references/metadata-examples.md`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *CustomMetadata* and *CustomMetadataValue*, pp. 748–752 (the `.md` suffix and `customMetadata` folder, record naming without `__mdt`, the "Customize Application" permission for records, the full `protected` access table, the `xsi:type` mapping table, `xsi:nil` versus an omitted `<values>` block, `EntityDefinition` / `FieldDefinition` value semantics, and the scale-0 Number double behaviour) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *CustomField* `fieldManageability` and `metadataRelationshipControllingField`, and *Metadata Field Types* `FieldType` (the `Locked` / `DeveloperControlled` / `SubscriberControlled` enum available only on custom metadata type fields, the `MetadataRelationship` field type, and the manageability coupling between entity-definition and field-definition fields) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *SchemaSettings* and *PermissionSet* / *Profile* `customMetadataTypeAccesses` (`enableAdvancedCMTSecurity` restricting values to Apex, flow, and formula operations; `PermissionSetCustomMetadataTypeAccess.enabled` gating record readability from API 47.0) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — *Custom Metadata Type__mdt*, pp. 77–79 (supported calls limited to `describeSObjects()`, `describeLayout()`, `query()`, `retrieve()`; the `DeveloperName` naming rules; `isProtected`, `MasterLabel`, `QualifiedApiName`, `NamespacePrefix`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Reference Guide — *Custom Metadata Type Methods* (`getAll()` and the three `getInstance()` overloads, their signatures and return types, and the 255-character truncation on every field returned by the cached accessors) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/
- Apex Developer Guide — *Execution Governors and Limits* and *Apex Metadata API* (custom metadata records can have unlimited SOQL queries in a single Apex transaction; records of custom metadata types are a supported Apex metadata deployment type; `DescribeSObjectResult.isAccessible()` behaviour change in API 54.0) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide — Custom Metadata Types (HTML edition) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custommetadata.htm
- Salesforce Well-Architected Overview (the Operational Excellence, Reliability, and Security framing used above) — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
