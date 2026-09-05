# Well-Architected Notes — Permission Set Architecture

## Relevant Pillars

### Security

Permission-set architecture is a Security concern because it is the control plane for feature access. Least privilege depends on capability boundaries, license-aware assignment, and avoiding profile drift that grants more than intended.

### Operational Excellence

Well-run access models reduce admin toil, make audits faster, and allow repeatable onboarding and offboarding. PSG-based bundle design is an operational tool as much as a security one.

### Reliability

Access changes are production changes. An architecture built on reusable bundles is easier to test and less likely to break user workflows when one entitlement changes.

## Architectural Tradeoffs

- **Thin profiles vs short-term convenience:** Keeping profiles minimal takes more design discipline up front, but it prevents long-term access sprawl.
- **Reusable PSGs vs many direct assignments:** Direct assignment is faster in the moment, but PSGs scale better for review, provisioning, and change management.
- **Shared bundles plus muting vs cloned bundles:** Muting preserves reuse, while cloned bundles can be clearer for radically different personas. Use muting sparingly.

## Anti-Patterns

1. **Profile per persona or exception** — this produces brittle access drift and makes every feature change a profile-maintenance task.
2. **Giant permission sets with no capability ownership** — access becomes impossible to review because one metadata object grants unrelated privileges.
3. **Muting-first architecture** — excessive subtractive exceptions hide the fact that the base bundle model is wrong.

## Official Sources Used

- Metadata API Developer Guide, `PermissionSet` metadata type — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (element list and API versions in `references/metadata-examples.md`; the `license` vs deprecated `userLicense` split; the "include all of its metadata to avoid accidentally overwriting the permission set's contents" warning behind the partial-file gotcha; API 40.0 disabling unlisted user permissions)
- Metadata API Developer Guide, `PermissionSetGroup` metadata type — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`permissionSets`, `mutingPermissionSets` API 46.0+, `hasActivationRequired` API 53.0+, the `status` enum `Updated` / `Outdated` / `Updating` / `Failed`, and the sample showing that a group carries no permissions of its own)
- Metadata API Developer Guide, `MutingPermissionSet` metadata type — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf ("settings enabled by MutingPermissionSet are turned off for the permission set group that it's a component of" — the inverted-read gotcha and the "Muting And Exceptions Need Governance" concept)
- Metadata API Developer Guide, Sample package.xml Manifest Files → Managed Component Access — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf ("when retrieving object or field permissions, you must also retrieve the associated object"; the `standard__` prefix for standard apps and `standard-<Object>` for standard tabs used in the examples)
- Object Reference, `PermissionSet` standard object (Usage, User Licenses, Child Objects, Associated Profiles) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (leave `LicenseId` empty for mixed-license assignment; `IsOwnedByProfile`; the "absence of a record indicates no access" model behind the negative-query gotcha)
- Object Reference, `ObjectPermissions` and `FieldPermissions` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the CRUD dependency chain and `PermissionsEdit` requiring `PermissionsRead`; the `Modify All Data` `000`-Id behaviour; verification SOQL in `references/metadata-examples.md`)
- Object Reference, `PermissionSetAssignment` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (`PermissionSetGroupId` API 45.0+, `ExpirationDate` API 52.0+ — the assignment examples and the "should any of this expire?" question)
- Object Reference, `SessionPermSetActivation` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf ("if you include session-based permission sets in a permission set group, the permissions in them don't require session-based activation" — the session-activation gotcha and the decision-guidance row)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (pillar framing for the Security / Operational Excellence / Reliability sections above)
