# Well-Architected Mapping: Permission Sets vs Profiles

---

## Pillars Addressed

### Security

**Principle: Least Privilege**
Every user should have exactly the access they need for their role — no more. The Permission Set model enables this more precisely than Profiles because access is additive and individually assignable.

- WAF check: Are users granted only the objects and fields required for their job function?
- WAF check: Is there an audit trail for permission changes? (PSG assignment logs are queryable)
- WAF check: Are temporary elevated permissions tracked and time-bound?

**How this skill addresses it:**
- The Decision Matrix prevents over-assignment by clarifying when NOT to use Profiles for feature access
- The Minimum Access base profile pattern eliminates profile-as-feature-grant
- Naming conventions make permission scope visible at a glance

**Risk of not following this:** Users retain access from old roles (role creep). Security audits fail. Data exposure through fields users shouldn't see.

### Operational Excellence

**Principle: Maintainability at Scale**
A permission model that requires creating a new Profile every time a new team is onboarded is not maintainable. PSGs enable role changes with a single assignment operation.

- WAF check: Can access be changed without a profile reassignment (which affects all other users on that profile)?
- WAF check: Is there a documented permission model that a new Admin can understand?
- WAF check: Are permission assignments auditable via SOQL?

**How this skill addresses it:**
- Mode 2 (Audit and Migrate) provides a systematic approach to reducing profile count
- SOQL examples make the current state queryable and auditable
- Naming conventions make the permission model self-documenting

**Risk of not following this:** Profile sprawl (50+ profiles in orgs older than 5 years). Access changes require testing entire profiles. No clear audit trail.

**Trade-off after the June 2026 retirement cancellation:** the platform no longer supplies a forcing function. With the Spring '26 retirement of permissions in profiles cancelled and no replacement date, a profile decomposition has to be justified on these Well-Architected grounds alone — auditability, single-operation role changes, least privilege — and it now competes with every other backlog item on business value rather than jumping the queue as compliance work. Budget it as maintainability investment, and prioritise the profiles where sprawl is actually costing something (frequent role changes, failed access audits) over a uniform org-wide sweep.

---

## Pillars Not Addressed

- **Performance** — Permission model design doesn't directly affect query/page performance.
- **Scalability** — Relevant only in the sense that profile sprawl becomes unmanageable at scale; the PSG model scales better administratively.
- **Reliability** — Not directly relevant to permission model design.
- **User Experience** — Indirectly relevant (users seeing too many or too few fields affects UX), but this skill doesn't address UX design.

---

## Salesforce Well-Architected Reference

**Security pillar:** [architect.salesforce.com/well-architected/security](https://architect.salesforce.com/well-architected/security)

Key principle applied: *"Grant the least amount of access necessary to accomplish the task."*

**Relevant Salesforce guidance:**
- Salesforce Help: User Permissions and Access
- Trailhead: Manage User Profiles and Permission Sets
- Salesforce Help 003834041: Permissions in Profiles Retirement Cancelled (supersedes any Profile Retirement FAQ you may have bookmarked)

## Official Sources Used

- [Metadata API Developer Guide (v62 PDF), `Profile` metadata type](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — the authoritative field table behind the profile-only element list in `references/metadata-examples.md`: `loginHours`, `loginIpRanges`, `layoutAssignments`, `categoryGroupVisibilities`, `loginFlows`, `custom`, and the `default` child of `applicationVisibilities` / `recordTypeVisibilities`. Also the source for the overlay-deployment rule ("we designed Profile metadata deployment to overlay the existing Profile settings"), the retrieve rule ("the returned `.profile` files only include security settings for the other metadata types referenced in the retrieve request. Exceptions include user permissions, IP address ranges, and login hours"), the empty-profile-deploy inheritance of the standard Minimum Access - Salesforce profile at API 60.0+, and "In API version 50.0 and later, editing standard objects on standard profiles is disabled"
- [Metadata API Developer Guide (v62 PDF), `PermissionSet` and `PermissionSetGroup` metadata types](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — the opposing field table: `label`, `license`, `hasActivationRequired`, `tabSettings` and its `Available` / `None` / `Visible` enum, the required-field marking on `PermissionSetObjectPermissions`, the `viewAllFields` suppression of `fieldPermissions`, the API 40.0 "all content exposed in Metadata API is included" retrieve/deploy rule, and the framing statement this whole skill rests on — "You can use permission sets to grant access but not to deny access"
- [Object Reference for the Salesforce Platform (v62 PDF), `PermissionSet` standard object](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) — `IsOwnedByProfile`, `ProfileId` and the "Associated Profiles" section: every profile is associated with a permission set that stores its user, object and field permissions, queryable but not modifiable, with the caveat not to depend on the `Name` and `Label` those rows return. Also the `ObjectPermissions` / `FieldPermissions` child-object model in which absence of a record means no access
- [Object Reference for the Salesforce Platform (v62 PDF), `PermissionSetAssignment` standard object](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) — the licence-match constraint that blocks a mid-migration assignment ("if the PermissionSet has a `UserLicenseId`, its `UserLicenseId` and the Profile `UserLicenseId` must match"), the guidance to leave `LicenseId` empty for mixed-licence populations, and `ExpirationDate` / `IsActive` / `IsRevoked` as the audit-trail fields behind the Operational Excellence checks above
- [Object Reference for the Salesforce Platform (v62 PDF), `Profile` standard object](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) — `UserLicenseId` and `UserType` as the licence ceiling that bounds everything a permission set can add, and the recommendation to create custom profiles through the `Profile` SOAP object rather than the metadata type because it produces an empty profile
- Salesforce Well-Architected — Security pillar — least-privilege and governance framing for the pillar mapping above
- [Salesforce Help 003834041 — "Permissions in Profiles Retirement Cancelled" (published 6 Jun 2026)](https://help.salesforce.com/s/articleView?id=003834041&language=en_US&type=1) — confirms the Spring '26 retirement of permissions in profiles was cancelled with no replacement end-of-life date, that profile-based permissions are still supported ("for now", in the article's words), that Salesforce now only *recommends* a permission set–led model, and enumerates the six settings it assigns to profiles (default assigned apps, default record types and page layouts, login hours, login IP ranges, password policies, session settings) (verified 2026-08-13)
