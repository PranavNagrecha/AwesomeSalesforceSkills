# Well-Architected Mapping: Einstein Analytics Basics

## Pillars Addressed

### User Experience

Choosing the right analytics tool prevents users from getting either underpowered reports or over-engineered dashboards.

- Clear tool selection keeps the experience understandable for the target audience.
- Role-focused dashboards reduce noise and improve decision speed.

### Operational Excellence

CRM Analytics only succeeds when refresh ownership, licensing, and support responsibilities are explicit.

- Dataset refresh design prevents stale-data surprises.
- Clear ownership for analytics assets makes failures diagnosable.

### Scalability

The skill pushes teams away from stretching standard reports past their practical limits.

- Heavier calculations and large-volume analysis are handled with the right platform.
- Tool selection based on growth prevents expensive rework later.

## Pillars Not Addressed

- **Security** - security is discussed only insofar as analytics access and sharing affect dashboard correctness.
- **Reliability** - this skill assumes source-data correctness and reconciliation are handled elsewhere.

## Official Sources Used

Read for this revision (2026-10-03):

- Analytics Platform Setup Guide (Spring '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_setup.pdf. Edition availability; licences and prebuilt permission sets; internal Integration User and Security User; Basic and Advanced setup procedures; user permission table; CRM Analytics Limits (row allocations, dataset limits, recipe and dataflow limits); CRM Analytics Limitations (localization, single currency, field-level security).
- Analytics Security Implementation Guide (Spring '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_security.pdf. Row-level security with security predicates, sharing inheritance and its backup predicate, editing security on the dataset, `$User` session rule.
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. AnalyticsSettings (`enableInsights`, `canAccessAnalyticsViaAPI`, `enableWaveMulticurrency`, `Analytics.settings` file, manifest example); Wave metadata type names.
- Salesforce Object Reference, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. PermissionSetLicense, PermissionSetLicenseAssign, and UserLicense fields used in the licence inventory queries.

Listed in the original version without links and not re-read: Salesforce Well-Architected Overview; Integration Patterns (cross-system analytics boundary framing).
