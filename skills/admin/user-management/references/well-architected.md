# Well-Architected Notes — User Management

## Relevant Pillars

- **Security** — User management is a foundational security domain. Every user's license, profile, role, and login restrictions directly determines what data they can read, edit, and delete. Misconfigured user accounts — wrong license type, overly permissive profile, missing IP restrictions — are a leading cause of data exposure incidents in Salesforce orgs. Applying least-privilege access through the correct license/profile combination and restricting login to known IP ranges reduces attack surface.

- **Operational Excellence** — Consistent user provisioning and offboarding procedures reduce admin burden, prevent access drift, and make auditing tractable. Delegated administration enables scalable user lifecycle management without concentrating all authority in a single System Administrator.

## Architectural Tradeoffs

**Delegated administration vs. additional System Admins:** Granting System Administrator profile to managers for user management is tempting but grants unrestricted access to all configuration, data, and settings. Delegated administration scopes authority to specific profiles and fields. Prefer delegated administration for any non-admin who only needs user lifecycle management.

**Profile-based login restrictions vs. network-level controls:** Login IP ranges and Login Hours on profiles are a Salesforce-native control layer but they apply only at login time and do not terminate active sessions. For high-security requirements, pair them with network firewall rules, SSO enforcement, and session timeout policies.

**Chatter Free vs. Salesforce license for low-usage accounts:** Chatter Free licenses cost nothing but cannot be upgraded to full licenses in-place. If any future CRM access is possible, provisioning a full license (left inactive when not needed) avoids a destructive license-type migration later.

## Anti-Patterns

1. **Using System Administrator profile for non-admin users who need extended permissions** — Granting System Administrator is frequently used as a shortcut when a user needs access to a specific Setup area or custom metadata. This exposes the entire org configuration to that user. Use permission sets, custom profiles, or delegated administration to scope access precisely.

2. **Deactivating users without pre-deactivation cleanup** — Deactivating a user without removing them from queues, reassigning owned records, and clearing open approval steps creates immediate operational problems: stuck approval workflows, case routing gaps, and orph aned record ownership. Always freeze → clean up → deactivate.

3. **Setting login hours without also configuring session termination** — Configuring Login Hours on profiles without enabling session logout at the boundary gives a false sense of access restriction. Users already logged in are unaffected. The session settings must be configured separately to actually enforce an end-of-access boundary.

## Official Sources Used

- Salesforce Help — Manage Salesforce Users: https://help.salesforce.com/s/articleView?id=sf.admin_users.htm
- Salesforce Help — User Licenses: https://help.salesforce.com/s/articleView?id=sf.users_understanding_license_types.htm
- Salesforce Help — Delegated Administration: https://help.salesforce.com/s/articleView?id=sf.delegating_admin_responsibilities.htm
- Salesforce Help — Set Login Restrictions: https://help.salesforce.com/s/articleView?id=sf.admin_loginrestrict.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
