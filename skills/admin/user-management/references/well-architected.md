# Well-Architected Notes — User Management

## Relevant Pillars

- **Security** — User management is a foundational security domain. Every user's license, profile, role, and login restrictions directly determines what data they can read, edit, and delete. Misconfigured user accounts — wrong license type, overly permissive profile, missing IP restrictions — are a leading cause of data exposure incidents in Salesforce orgs. Applying least-privilege access through the correct license/profile combination and restricting login to known IP ranges reduces attack surface.

- **Operational Excellence** — Consistent user provisioning and offboarding procedures reduce admin burden, prevent access drift, and make auditing tractable. Delegated administration enables scalable user lifecycle management without concentrating all authority in a single System Administrator.

## Architectural Tradeoffs

**Delegated administration vs. additional System Admins:** Granting System Administrator profile to managers for user management is tempting but grants unrestricted access to all configuration, data, and settings. Delegated administration scopes authority to specific profiles and fields. Prefer delegated administration for any non-admin who only needs user lifecycle management.

**Profile-based login restrictions vs. network-level controls:** Login IP ranges and Login Hours on profiles are a Salesforce-native control layer but they apply only at login time and do not terminate active sessions. For high-security requirements, pair them with network firewall rules, SSO enforcement, and session timeout policies.

**Chatter Free vs. Salesforce license for low-usage accounts:** Chatter Free licenses cost nothing but cannot be upgraded to full licenses in-place. If any future CRM access is possible, provisioning a full license (left inactive when not needed) avoids a destructive license-type migration later.

**Reclaiming licences has a second-order cost.** The org's daily asynchronous Apex ceiling
(`DailyAsyncApexExecutions`) is "250,000 or the number of applicable user licenses in your org
multiplied by 200, whichever is greater" (App Limits Cheat Sheet), and the applicable types include
full Salesforce and Salesforce Platform licences, App Subscription, Chatter Only, Identity and Company
Communities. An org above 1,250 licences is running on the licence-derived number, so a large
deactivation sweep lowers the async ceiling as well as the bill. Model the batch and Queueable load
before treating unused seats as pure savings.

**Green tests are not licence headroom.** The Apex Developer Guide states that `runAs` "ignores user
license limits. You can create users with `runAs` even if your organization has no additional user
licenses." A provisioning class with full coverage proves the field mapping is right and proves
nothing about whether production can seat the user. Licence capacity is a pre-load query against
`UserLicense` and `PermissionSetLicense`, never a test result.

## Anti-Patterns

1. **Using System Administrator profile for non-admin users who need extended permissions** — Granting System Administrator is frequently used as a shortcut when a user needs access to a specific Setup area or custom metadata. This exposes the entire org configuration to that user. Use permission sets, custom profiles, or delegated administration to scope access precisely.

2. **Deactivating users without pre-deactivation cleanup** — Deactivating a user without removing them from queues, reassigning owned records, and clearing open approval steps creates immediate operational problems: stuck approval workflows, case routing gaps, and orph aned record ownership. Always freeze → clean up → deactivate.

3. **Setting login hours without also configuring session termination** — Configuring Login Hours on profiles without enabling session logout at the boundary gives a false sense of access restriction. Users already logged in are unaffected. The session settings must be configured separately to actually enforce an end-of-access boundary.

## Official Sources Used

- Object Reference (Summer '26 / v62) — **User** object: field table (`Username` globally unique and
  email-shaped, `Alias`/`Email`/`LastName`/`TimeZoneSidKey`/`LocaleSidKey`/`EmailEncodingKey`/`LanguageLocaleKey`/`ProfileId`
  Required, `ProfileId` change implies a licence change), Special Access Rules (Manage Internal Users
  vs Manage External Users), and the **Deactivate Users** usage note (users can never be deleted; API
  does not auto-remove team membership; `EntitySubscription` soft-delete on deactivation and hard-delete
  on mass deactivation). Supports "Core Concepts", Gotchas 9 and 11, and `references/metadata-examples.md`
  sections 1, 8 and 9. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference — **UserLicense**, **PermissionSetLicense**, **PermissionSetLicenseAssign**: the
  `UsedLicenses` wording that separates "assigned to active users" from "currently assigned to users",
  and the note that `UserLicense.UsedLicenses` is not filterable in API v64.0+. Supports Gotcha 6 and
  the licence-verification queries in `references/metadata-examples.md` section 7.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference — **UserLogin**, **LoginHistory**, **UserRole**, **Group**/**GroupMember**: freeze
  is an `update()`-only operation on `UserLogin` whose `UserId` cannot be updated; `LoginHistory` has a
  closed filterable-field list that excludes `Status` and `SourceIp`; `Group.Type` distinguishes `Queue`
  from `Regular`; `GroupMember` records direct membership only. Supports Gotcha 7 and
  `references/metadata-examples.md` sections 8, 9 and 10.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Metadata API Developer Guide (v62) — **Role** / **RoleOrTerritory** (`.role` suffix, `roles/` directory,
  `parentRole`, the `caseAccessLevel`/`contactAccessLevel`/`opportunityAccessLevel` enums and their
  Public Read/Write inertness) and **Profile** (`userLicense`, `ProfileLoginHours` minutes-since-midnight
  divisible by 60, `ProfileLoginIpRange`, and the empty-`loginHours`-tag deletion rule). Supports
  Gotcha 10 and `references/metadata-examples.md` sections 2, 3 and 4.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide (v62) — **Using the runAs Method** and **Mixed DML Operations in Test Methods**:
  `User` is a setup sObject, `runAs` legalises mixed DML, `runAs` "ignores user license limits", and every
  `runAs` call consumes a DML statement. Supports the "test users prove nothing about licence headroom"
  tradeoff below and `references/metadata-examples.md` section 5.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- REST API Developer Guide (v62) — **Create Records Using sObject Collections**: the 200-record cap,
  ordered processing, and the rule that "you can't create records for multiple object types in one call
  when one of the types is related to a feature in the Salesforce Setup area" — mixed DML restated for
  REST. Supports `references/metadata-examples.md` section 6.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Data Loader Guide (v62) — **Configure Data Loader → Settings**: import batch size 200 (SOAP) / 10,000
  (Bulk API) / automatic (Bulk API 2.0), and the Insert Null Values note requiring a literal `#N/A` to
  null a field under either Bulk API. Supports Gotcha 8 and the load commands in
  `references/metadata-examples.md` section 1.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf
- Salesforce App Limits Cheat Sheet — **Salesforce Platform Apex Limits**: `DailyAsyncApexExecutions` is
  "250,000 or the number of applicable user licenses in your org multiplied by 200, whichever is greater."
  Supports the licence-reclamation tradeoff below.
- Salesforce Well-Architected — Overview:
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
