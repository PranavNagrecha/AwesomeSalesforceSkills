# Well-Architected Notes — Guest User Security

## Relevant Pillars

- **Security** — Guest user hardening is a first-order security requirement for any public-facing Experience Cloud site. Misconfigured guest profiles are one of the most common vectors for unintended data exposure in Salesforce orgs. Every guest profile permission and Apex class reachable from guest context must be explicitly reviewed.
- **Operational Excellence** — Auditing guest profiles after each deployment and after each Experience Cloud site addition prevents permission drift. A documented guest security baseline makes audits repeatable.

## Architectural Tradeoffs

**OWD Public Read Only vs guest sharing rules:** Setting OWD to Public Read Only gives guest users read access to all records of that type — simple to configure, but broad. Guest sharing rules can grant more targeted access (e.g., only records related to a specific account) but are limited to Read Only since Spring '21 and cannot grant access to Private OWD records. For most use cases, Public Read Only OWD with Apex filtering is the cleaner pattern.

**`with sharing` + `WITH USER_MODE` vs manual FLS checks:** `WITH USER_MODE` in SOQL is declarative and enforces both sharing and FLS in one modifier. Manual `Schema.SObjectType.Field.isAccessible()` checks require checking every field individually and are easier to misconfigure (a missed field check becomes a data leak). Prefer `WITH USER_MODE` for all guest-facing Apex.

## Anti-Patterns

1. **`without sharing` Apex reachable from guest sessions** — a single `without sharing` class called from a guest LWC or Apex REST endpoint ignores the sharing model entirely, exposing records based only on the SOQL filter logic. This is a full-org data read risk for public users.
2. **Granting Create/Edit to guest profile "temporarily" for testing** — temporary elevated permissions on the guest profile frequently persist to production. The guest profile should have only the minimum permissions needed for the public use case. Test with a separate internal user that mirrors guest permissions.
3. **Not auditing permission sets assigned to the guest user** — since Spring '22, permission sets can be assigned to guest users. A permission set that grants access to sensitive objects silently elevates the guest user's effective permissions beyond what the profile shows.

## Official Sources Used

- Salesforce Security Guide (Guest User Access) — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Secure Guest User Record Access — https://help.salesforce.com/s/articleView?id=sf.networks_secure_guest_user_record_access.htm&type=5
- Communities Developer Guide (Guest User) — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_secur_setup.htm
- Apex Security and Sharing (WITH USER_MODE) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_enforce_usermode.htm
