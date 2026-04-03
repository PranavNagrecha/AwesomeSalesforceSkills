# Well-Architected Notes — Data Model Documentation

## Relevant Pillars

- **Operational Excellence** — The primary pillar for this skill. An undocumented data model creates operational risk: integrations break on renamed or repurposed fields, new admins make incorrect changes, and audits fail when field ownership cannot be demonstrated. Keeping a current, accurate field inventory and ER diagram is a core operational excellence practice.
- **Security** — FLS documentation is part of a security review. Without documented field-level permissions, you cannot confirm that sensitive fields (SSNs, payment references, health data) are restricted to the correct profiles and permission sets. The security architecture review skill depends on accurate FLS documentation.
- **Reliability** — Integration reliability depends on stable, well-documented field contracts. When a field's purpose is documented (external ID, integration sync key, deprecated legacy field), downstream systems can make appropriate decisions about consuming or ignoring it. Undocumented fields are changed or deleted without awareness of downstream impact.

## Architectural Tradeoffs

**Complete vs. scoped documentation:** Documenting every field in a large org (thousands of custom fields) is a multi-week project. Scoping documentation to the objects used by a specific integration, process, or team delivers value faster. The tradeoff is that out-of-scope objects remain a risk. Best practice is to start with the objects touched by active integrations and high-risk processes, then expand coverage iteratively.

**Living documentation vs. point-in-time snapshot:** A spreadsheet captured today will drift from the real schema within weeks as admins add and rename fields. Documentation stored as version-controlled metadata (via SFDX source format in Git) stays current because schema changes produce diffs. The tradeoff is that this requires a Git-based development workflow.

## Anti-Patterns

1. **Documentation that only covers custom objects** — Standard objects like Account and Contact are modified heavily in most orgs. Custom fields added to standard objects carry the same documentation obligation as fields on custom objects. Omitting them leaves integration and audit gaps.
2. **ER diagrams built without checking for polymorphic lookups** — Diagrams produced from Schema Builder alone miss polymorphic relationships (Task WhoId/WhatId). These are among the most commonly misunderstood relationships in the Salesforce data model. Diagrams that omit or misrepresent them mislead integration architects and developers.
3. **No ownership column in the field inventory** — A field inventory without a team or system owner column becomes stale immediately. Fields that were added for a project that no longer exists sit undocumented in perpetuity. Each custom field should have a documented owner who is responsible for its accuracy and who should be consulted before the field is modified.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm — used for standard object and field type definitions, cardinality rules, and polymorphic lookup behavior
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — used for CustomObject metadata structure, field XML elements, and FLS storage in Profile/PermissionSet metadata
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — used for Operational Excellence pillar framing and documentation as a quality practice
