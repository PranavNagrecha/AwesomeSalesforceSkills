# Well-Architected Notes — Guest User Security

## Relevant Pillars

- **Security** — Guest user hardening is a first-order security requirement for any public-facing Experience Cloud site. Misconfigured guest profiles are one of the most common vectors for unintended data exposure in Salesforce orgs. Every guest profile permission and Apex class reachable from guest context must be explicitly reviewed.
- **Operational Excellence** — Auditing guest profiles after each deployment and after each Experience Cloud site addition prevents permission drift. A documented guest security baseline makes audits repeatable.

## Architectural Tradeoffs

**Broad vs narrow guest user sharing rule criteria:** OWD is not a lever here. Guest org-wide defaults are Private for every object and can't be changed, and guest user sharing rules are the only mechanism that grants a guest any record access. The real tradeoff is criteria width: a rule like `Id != null` is trivial to write and effectively republishes the whole object to the internet, while `Is_Public__c = true` costs a field and a maintenance habit but bounds the blast radius to records someone deliberately marked public. Prefer a dedicated boolean or record type in the criteria over a filter that happens to be true today. Budget for the limit — guest user sharing rules count toward the 50 criteria-based sharing rules per object.

**`with sharing` + `WITH USER_MODE` vs manual FLS checks:** `WITH USER_MODE` in SOQL is declarative and enforces both sharing and FLS in one modifier. Manual `Schema.SObjectType.Field.isAccessible()` checks require checking every field individually and are easier to misconfigure (a missed field check becomes a data leak). Prefer `WITH USER_MODE` for all guest-facing Apex.

## Anti-Patterns

1. **`without sharing` Apex reachable from guest sessions** — a single `without sharing` class called from a guest LWC or Apex REST endpoint ignores the sharing model entirely, exposing records based only on the SOQL filter logic. This is a full-org data read risk for public users.
2. **Granting Create/Edit to guest profile "temporarily" for testing** — temporary elevated permissions on the guest profile frequently persist to production. The guest profile should have only the minimum permissions needed for the public use case. Test with a separate internal user that mirrors guest permissions.
3. **Not auditing permission sets assigned to the guest user** — permission sets can be assigned to guest users and always could; Spring '22 restricted rather than introduced this. A permission set that grants access to sensitive objects silently elevates the guest user's effective permissions beyond what the profile shows.

## Official Sources Used

- Salesforce Security Guide (Guest User Access) — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Secure Guest Users' Sharing Settings and Record Access ("guest users have org-wide defaults set to Private for all objects"; "Guest user sharing rules are a special type of criteria-based sharing rule and the only way to grant record access to unauthenticated guest users"; "The Secure guest user record access setting is enabled in all Salesforce orgs with Experience Cloud sites and can't be disabled") — https://help.salesforce.com/s/articleView?id=platform.networks_secure_guest_user_sharing.htm&type=5
- Guest User Security Policies and Timelines (Secure guest user record access — Winter '21; View All / Modify All / edit / delete removed from guest users — Spring '21) — https://help.salesforce.com/s/articleView?id=sf.networks_guest_policies_timelines.htm&type=5
- Best Practices and Considerations When Configuring the Guest User Profile ("Have org-wide defaults set to Private for all objects. This access level can't be changed."; "Never assign the View All Records or Modify All Records permission to guest users."; "The only object permissions allowed for guest users are read and create.") — https://help.salesforce.com/s/articleView?id=platform.networks_guest_profile_best_practices.htm&type=5
- "View All" and "Modify All" Permissions Overview (View All Fields = "Viewing all fields and field data for a specific object"; "View All Data, Modify All Data, and View All Records, Modify All Records, or View All Fields for a given object can't be assigned to external users.") — https://help.salesforce.com/s/articleView?id=platform.users_profiles_view_all_mod_all.htm&type=5
- Trailhead, Admin Certification Maintenance (Spring '25) — Get Hands-on with the View All Fields Permission ("On the Object Settings page for a specific object, enable the View All Fields permission"; "Users are automatically granted access to any new fields created for the object.") — https://trailhead.salesforce.com/content/learn/modules/administrator-certification-maintenance-spring-25/get-hands-on-with-the-view-all-fields-permission
- Communities Developer Guide (Guest User) — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_secur_setup.htm
- Apex Security and Sharing (WITH USER_MODE) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_enforce_usermode.htm
- Salesforce Help — Guest User Security Policies and Timelines (Spring '21 permission removals; Spring '22 permission-set-licence restriction; Winter '23 enforcement of "Remove Guest User Assignments from Permission Sets Associated with Permission Set Licenses with Restricted Object Permissions") — https://help.salesforce.com/apex/HTViewHelpDoc?id=networks_guest_policies_timelines.htm
