# Well-Architected Notes — Data Classification Labels

## Relevant Pillars

- **Security** — Data classification is foundational to a layered security posture. The WAF Security pillar recommends classifying data by sensitivity as a prerequisite for making informed decisions about encryption, access control, and audit trail coverage. Classification labels make FLS and Shield decisions traceable to a documented sensitivity tier rather than ad-hoc judgment. A field labeled `Restricted` or `MissionCritical` signals that FLS, encryption, and long-term audit trail must all be evaluated for that field.

- **Operational Excellence** — Classification metadata stored in source control and deployed via Metadata API is an operational excellence practice. It enables repeatable, auditable, pipeline-driven classification changes rather than manual UI edits that leave no trace in version history. The `BusinessOwnerId` and `BusinessStatus` attributes support lifecycle management — tracking deprecated fields and their responsible owners prevents accumulation of unmanaged sensitive data.

## Architectural Tradeoffs

**Classification as documentation vs. classification as enforcement:**
The platform makes classification purely informational. Teams that treat it as an enforcement mechanism will have unprotected sensitive fields. Teams that use it correctly — as a documentation and discovery layer feeding into FLS, encryption, and audit trail decisions — gain a tractable governance program. The tradeoff is that classification adds overhead with no automatic protection; all enforcement must be separately implemented and maintained.

**Tooling API vs. Metadata API for classification management:**
Tooling API is fast and convenient for reading classification state at scale, but it cannot reliably write `ComplianceGroup`. Metadata API is slower and requires a full deploy cycle but is the only reliable write path for all four classification attributes. Audit-and-deploy pipelines should use Tooling API for read/validation and Metadata API for writes.

**Einstein Data Detect convenience vs. manual precision:**
Data Detect accelerates discovery of PII and compliance-relevant fields but is imprecise — it matches on field naming patterns and may generate false positives (fields named generically) or miss fields with non-obvious names. Manual review of Data Detect recommendations is required; wholesale acceptance without human review will produce an inaccurate classification record.

## Anti-Patterns

1. **Substituting classification labels for access controls** — Marking a field `Restricted` and treating that as a security control is an architectural anti-pattern. Classification labels are not evaluated by the platform's access control system. Any compliance program that cites "field classified as Restricted" without also showing FLS restrictions on that field has a documentation-only control with no enforcement backing.

2. **Manually managing classification in Setup without source control** — Applying classification labels through the Setup UI creates an org state that is invisible to source control and will be overwritten the next time the field is deployed from an unclassified SFDX project. Classification must be in `.field-meta.xml` files checked into version control to survive the deployment lifecycle.

3. **Running Data Detect once and treating classification as complete** — Einstein Data Detect is a discovery tool, not a one-time classification program. New custom fields are added continuously; new compliance frameworks may expand the scope of regulated data. Classification should be an ongoing practice: new fields classified at creation time, and periodic Tooling API audits surfacing unclassified fields for review.

## Official Sources Used

- Salesforce Help: Set Up Data Classification — https://help.salesforce.com/s/articleView?id=sf.data_classification_set_up.htm&type=5
- Salesforce Help: Data Classification Metadata Fields — https://help.salesforce.com/s/articleView?id=sf.data_classification_metadata_fields.htm&type=5
- Salesforce Help: Einstein Data Detect — https://help.salesforce.com/s/articleView?id=sf.einstein_data_detect.htm&type=5
- Salesforce Developer: Tooling API FieldDefinition — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_fielddefinition.htm
- Salesforce Metadata API: CustomField — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_field_types.htm
