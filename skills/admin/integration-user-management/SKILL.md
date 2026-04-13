---
name: integration-user-management
description: "Use when setting up or auditing dedicated Salesforce integration users — including the Salesforce Integration user license, API-only profile, permission set layering, MFA waiver configuration, and login monitoring. NOT for standard user management."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "How do I create a dedicated integration user that can only access the API and not the Salesforce UI?"
  - "Integration user is being blocked by MFA enforcement — how do I grant an exemption?"
  - "Should I use a System Administrator profile for an integration user to avoid permission issues?"
  - "How do I monitor which API calls are being made by the integration user?"
  - "What profile and license should I use for a MuleSoft integration user?"
tags:
  - integration-user
  - api-only
  - integration-user-management
  - mfa-waiver
  - permission-set
  - login-history
inputs:
  - "Integration system name and the Salesforce objects/fields it needs to access"
  - "Whether the org has MFA enforcement enabled"
  - "Current integration user license and profile configuration"
outputs:
  - "Integration user setup with Salesforce Integration license and API-only profile"
  - "Permission set configuration for least-privilege object and field access"
  - "MFA waiver configuration for the integration user"
  - "Login History monitoring query for auditing integration activity"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Integration User Management

This skill activates when a practitioner needs to set up, configure, or audit a dedicated Salesforce integration user — the dedicated API-only user identity that middleware, ETL tools, or external systems use to authenticate to Salesforce. It covers the correct license/profile combination, least-privilege permission layering, MFA waiver requirements, and login monitoring.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Dedicated integration users are mandatory for production integrations**: Shared user accounts or admin-profile integration users violate Salesforce security best practices and create audit and compliance risks. Every integration should have its own dedicated integration user.
- **Most common wrong assumption**: Granting the System Administrator profile or a cloned admin profile to an integration user "for simplicity." This bypasses the API-only flag (grants interactive login capability), grants access to all org data, and violates least-privilege. The correct approach is the Minimum Access - API Only Integrations profile plus targeted permission sets.
- **MFA waiver is not automatic**: Integration users are exempt from org-wide MFA enforcement, but this exemption must be explicitly granted. Integration users created after MFA enforcement is enabled do not automatically inherit the waiver and will be blocked unless it is applied.

---

## Core Concepts

### Salesforce Integration User License

The Salesforce Integration user license (also called the "Salesforce API Integration" license) is specifically designed for server-to-server integrations. Key characteristics:

- Cannot be used for interactive Salesforce UI login (no browser session capability).
- Requires the "Minimum Access - API Only Integrations" profile as the base profile.
- Consumes a dedicated user license, not a standard Salesforce license.
- Supports API access via username-password, OAuth client credentials, and JWT bearer flows.
- The license-profile combination enforces API-only access at the platform level — this is not configurable by admins.

### Minimum Access - API Only Integrations Profile

This profile is the mandatory base profile for Salesforce Integration user license accounts. It:
- Enforces API-only access (no Salesforce UI login).
- Grants no default object or field permissions (truly minimum access).
- Cannot be cloned or modified.
- All data access must be layered on via permission sets.

This profile-license combination ensures that even if the integration user's credentials are compromised, the attacker cannot access the Salesforce UI.

### Least-Privilege Permission Set Strategy

Because the base profile grants no object or field permissions, all access must be granted via permission sets following least-privilege:

1. Create a dedicated permission set for the integration (e.g., "MuleSoft Integration - Opportunity Access").
2. Grant only the specific object CRUD permissions the integration requires (no `Modify All Data`, no `View All Data` unless absolutely required).
3. Grant FLS access only to the specific fields the integration reads or writes.
4. Assign the permission set to the integration user.

For large integrations with many objects, multiple scoped permission sets (one per integration function) are preferred over a single broad permission set. This enables access to be revoked granularly if an integration function is decommissioned.

### MFA Waiver Configuration

If the org has MFA enforcement enabled, integration users must be explicitly exempted:

1. Navigate to Setup > Security > Identity Verification.
2. Under "MFA for API Logins," confirm the setting is "Required" or "Not Required."
3. For integration users that must be exempt: assign the "Salesforce API Integration" user permission or use the "Waive Multi-Factor Authentication for Exempt Users" permission in a permission set.

Integration users using certificate-based authentication (JWT bearer flow) or OAuth client credentials flow (no username/password) are inherently MFA-resistant because they do not use an interactive login flow.

### Login History Monitoring

Login History (Setup > Users > Login History) shows login attempts for all users including integration users:
- UI displays the most recent 20,000 records with a 6-month retention window.
- Full history is available via SOQL query on the `LoginHistory` object (API v21.0+).
- Key fields: `UserId`, `Status` (Success/Failed), `LoginType` (API, OAuth, etc.), `SourceIp`, `LoginTime`.

For detecting anomalous integration behavior:
- Monitor for failed login attempts (Status != "Success").
- Alert on login attempts from unexpected IP addresses (SourceIp not in known integration server range).
- Schedule periodic reports comparing actual login frequency against expected integration call patterns.

---

## Common Patterns

### Setting Up a New Integration User

**When to use:** A new integration system (MuleSoft, Informatica, custom middleware) needs a dedicated Salesforce identity.

**How it works:**
1. Purchase and provision a Salesforce Integration user license in Setup > Company Information.
2. Create a new user: Setup > Users > New User. Set License to "Salesforce Integration," Profile to "Minimum Access - API Only Integrations."
3. Create a permission set named after the integration system: `<IntegrationName>_Integration`.
4. In the permission set, grant object-level CRUD and FLS for only the specific fields the integration needs.
5. Assign the permission set to the user.
6. If MFA enforcement is enabled, configure the MFA waiver for the integration user.
7. Configure the connected app with "Admin approved users are pre-authorized" and assign the connected app to the integration user's permission set or profile.
8. Test authentication and API access as the integration user.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New integration needs Salesforce API access | Salesforce Integration license + Minimum Access - API Only Integrations profile | Enforces API-only at the platform level, least-privilege base |
| Integration user blocked by MFA | Configure MFA waiver explicitly for the user | MFA waiver is not automatic; must be explicitly granted |
| Integration needs access to specific objects | Targeted permission set for those objects only | Minimum Access profile grants no object permissions — all must be layered on |
| Quick fix: grant admin profile for integration | Never — violates least-privilege and security | Admin profile grants interactive login and all data access |
| Audit integration user activity | Query LoginHistory SOQL object | Setup UI shows 20K records; full history via API |
| Integration user needs to modify all records | Grant View All and Modify All only if technically required | Always justify in documentation; prefer object-level CRUD + sharing override |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the integration's data requirements** — Document which Salesforce objects and fields the integration reads, creates, updates, and deletes. This determines the minimum permission set scope.
2. **Provision the Salesforce Integration user license** — Confirm the org has available Salesforce Integration user licenses. If not, work with the account team to add them.
3. **Create the integration user** — In Setup > Users > New User, set License to "Salesforce Integration" and Profile to "Minimum Access - API Only Integrations." Use a service account email address that routes to a monitored team alias, not an individual.
4. **Create and configure a permission set** — Create a permission set named descriptively (e.g., `MuleSoft_Opportunity_Integration`). Add object CRUD permissions and FLS for only the required objects and fields. Assign to the integration user.
5. **Configure MFA waiver (if needed)** — If the org enforces MFA for API logins, grant the MFA waiver to the integration user via permission or user settings before testing authentication.
6. **Connect the user to a Connected App** — Ensure the integration's connected app is set to "Admin approved users are pre-authorized" and assigned to the integration user's permission set or profile.
7. **Test authentication and data access** — Authenticate as the integration user and make a test API call to each object the integration uses. Confirm the expected records are accessible and no unexpected objects or fields are visible.
8. **Document the integration user** — Record the user's username, assigned permission sets, connected apps, and MFA waiver status in the integration documentation. Schedule a quarterly review to confirm the access profile still reflects the integration's actual needs.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Salesforce Integration license assigned (not standard Salesforce license)
- [ ] Minimum Access - API Only Integrations profile assigned (no admin or cloned admin profile)
- [ ] Targeted permission set created with only required object/field access
- [ ] Permission set assigned to integration user
- [ ] MFA waiver configured if org enforces MFA for API logins
- [ ] Connected app assigned to integration user (if pre-authorized mode is used)
- [ ] Authentication tested successfully — API calls succeed, UI login is blocked
- [ ] Login History monitoring configured

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Admin profile integration users bypass the API-only flag** — Granting System Administrator or any profile without the "API Only User" flag to an integration user enables interactive login capability. If the credentials are compromised, an attacker can log into the Salesforce UI with admin privileges. The Minimum Access - API Only Integrations profile enforces API-only at the platform level — this cannot be replicated by cloning and modifying another profile.
2. **MFA waiver for integration users is not automatic** — When an org enables MFA enforcement, existing integration users may be grandfathered. But new integration users created after MFA enforcement is enabled do NOT automatically receive the waiver — they are blocked by MFA on their first authentication attempt. Explicitly configure the MFA waiver for every new integration user in an MFA-enforced org before testing authentication.
3. **Login History UI shows only 20,000 records** — The Setup > Login History UI is limited to the most recent 20,000 records. For high-frequency integrations making thousands of API calls per day, this limit is reached quickly and older login records become invisible in the UI. For full audit history, query the `LoginHistory` SOQL object via the API — it retains up to 6 months of data regardless of the UI limit.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration user configuration | License, profile, username, and service account email setup |
| Permission set definition | Object CRUD and FLS grants for the specific integration scope |
| MFA waiver configuration | Steps to configure MFA exemption for the integration user |
| LoginHistory monitoring query | SOQL query for auditing integration login activity |

---

## Related Skills

- integration-admin-connected-apps — Configure the connected app the integration user will authenticate through
- remote-site-settings — Configure the server-side callout allowlist for the integration's external endpoints
