# Well-Architected Mapping: Sharing and Visibility

## Pillars Addressed

### Security

Record-level access is a core Salesforce security boundary.

- Restrictive OWD plus explicit sharing reduces accidental overexposure.
- Auditing bypass permissions prevents security models from being undermined silently.

### Reliability

Sharing design depends on ownership, hierarchy, and group structure.

- Clean ownership models make sharing predictable.
- Public groups and rule design encode real collaboration patterns into the data model.

### Operational Excellence

A sharing model that requires constant manual rescue does not scale.

- Access debugging becomes faster when the model is layered and documented.
- Reducing exception-based sharing lowers admin support load.

## Pillars Not Addressed

- **Performance** - this skill flags recalculation risk, but it is not a query-optimization guide.
- **User Experience** - page visibility issues are adjacent, not the main focus here.

## Official Sources Used

- Metadata API Developer Guide (v62 PDF), `CustomObject` and the `SharingModel` field type — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the eight `sharingModel` values and their per-object narrowing, `externalSharingModel` from API 31.0, and `sharingModel` being settable through the API only from API 30.0 — `references/metadata-examples.md` step 1)
- Metadata API Developer Guide (v62 PDF), `SharingRules`, `SharingBaseRule`, `SharingCriteriaRule`, `SharingOwnerRule` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (required `accessLevel` / `label` / `sharedTo`, the required and uneditable `includeRecordsOwnedByAll`, and the one-file-per-object layout used in `references/metadata-examples.md` step 4)
- Metadata API Developer Guide (v62 PDF), `SharedTo` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the complete recipient element list, the absence of any `user` element — the basis for the checker's individual-user rule — and the `queue` and `guestUser` restrictions)
- Metadata API Developer Guide (v62 PDF), `Group` and `Queue` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf ("Members of the public group aren't migrated when you deploy the group type" and `doesIncludeBosses` as the per-group Grant Access Using Hierarchies switch, `Queue` from API 67.0 — gotchas 7 and 8)
- Metadata API Developer Guide (v62 PDF), `Role` / `RoleOrTerritory` and `SharingSet` / `AccessMapping` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`parentRole`, the three "other users' records associated with accounts you own" access levels and their unset default; sharing-set `objectField` / `userField` / `accessLevel` and the license list — `references/metadata-examples.md` steps 2 and 5)
- Object Reference for the Salesforce Platform (v62 PDF), `UserRecordAccess` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the restriction-rule blind spot, the 200-record cap, the Sharing Settings object list, and the SELECT-clause rules — gotcha 11 and `references/metadata-examples.md` step 7)
- Object Reference for the Salesforce Platform (v62 PDF), `AccountShare`, `CaseShare`, `OpportunityTeamMember`, and "Sharing and Custom Objects" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the `RowCause` picklist, Manual-only write access, sharing-set and `ImplicitChild` rows not being stored, no share object for master-detail children, and the API-versus-UI difference on opportunity owner change — gotchas 9, 10 and 12)
- Apex Developer Guide (v62 PDF), Apex Managed Sharing — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf ("Access level must be more permissive than the object's default" and the `FIELD_FILTER_VALIDATION_EXCEPTION` on `AccessLevel` — gotcha 6)
- `standards/decision-trees/sharing-selection.md` — the seven-step design sequence and Q1-Q9 routing this skill defers to for mechanism selection
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (the pillar framing above)
