# Well-Architected Mapping: Email Templates and Alerts

## Pillars Addressed

### User Experience

Operational emails are part of the product experience.

- Clear sender identity and subject lines improve trust.
- Focused content reduces support follow-up and ignored notifications.

### Reliability

Users depend on transactional emails to reflect real business events.

- Strict trigger logic reduces duplicate or missing notifications.
- Correct merge context prevents broken content at the moment of action.

### Operational Excellence

Email sprawl becomes governance debt quickly.

- Template ownership and sender governance reduce chaos.
- Consolidating overlapping alerts keeps maintenance manageable.

## Pillars Not Addressed

- **Security** - this skill touches sender governance and compliance awareness, not deep auth design.
- **Performance** - email design is rarely a compute bottleneck; the bigger issue is automation discipline.

## Official Sources Used

- Salesforce Well-Architected Overview — operational and user-facing notification design framing
- Metadata API Developer Guide — email template and alert metadata deployment behavior
- Metadata API Developer Guide: EmailTemplate (types, `uiType`, subject limits, no wildcard retrieval; PDF v62) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide: EmailTemplate — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_emailtemplate.htm
- Object Reference: OrgWideEmailAddress (`IsVerified`, `Purpose`, `IsAllowAllProfiles`; PDF v62) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
