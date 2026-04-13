# Gotchas — Integration User Management

## Gotcha 1: MFA Waiver Is Not Automatic for New Integration Users After MFA Enforcement

**What happens:** A new integration user is created in an org with MFA enforcement enabled. The integration's first authentication attempt is challenged for MFA, which the server-to-server integration cannot complete. Authentication fails. The existing integration users (created before MFA enforcement) continue to work normally because they received a grandfathered waiver.

**When it occurs:** Any time a new integration user is provisioned in an org that has already enabled MFA enforcement. Also occurs when an integration user's profile or license is changed, which may reset the waiver status.

**How to avoid:** After creating any new integration user in an MFA-enforced org, immediately configure the MFA waiver before testing authentication. Check the org's current MFA enforcement status first — if enforcement is enabled, the waiver configuration is a mandatory step, not optional.

---

## Gotcha 2: Admin Profile Grants Interactive Login — Defeating the API-Only Design

**What happens:** An integration user with System Administrator or a cloned admin profile can log into the Salesforce web UI through a browser, in addition to making API calls. Any person or system with the integration user's credentials can access the full Salesforce UI with admin privileges. This is invisible in standard security audits unless profile assignments are specifically checked.

**When it occurs:** Whenever an admin grants a non-API-only profile (System Administrator, Standard User, or any custom profile without the API-only flag) to an integration user for "simplicity" or to resolve permission errors quickly.

**How to avoid:** The Minimum Access - API Only Integrations profile is the only profile that enforces API-only access at the platform level for the Salesforce Integration user license. Never assign any other profile to a Salesforce Integration user. When permission errors occur, add a permission set — do not change the profile.

---

## Gotcha 3: Login History UI Truncates to 20,000 Records

**What happens:** An admin attempts to audit an integration user's login activity over the past month using Setup > Users > Login History. The history only shows records from the past few days — older records are not visible.

**When it occurs:** High-frequency integrations making thousands of API calls per day can exhaust the 20,000-record UI display limit within days. The records still exist in the platform (6-month retention) but are not visible in the Setup UI.

**How to avoid:** For full audit history on high-frequency integration users, use the SOQL LoginHistory object via the Salesforce API:
```soql
SELECT UserId, Status, LoginType, SourceIp, LoginTime 
FROM LoginHistory 
WHERE UserId = '<integration_user_id>'
ORDER BY LoginTime DESC
```
The API returns up to 6 months of login records regardless of the UI display limit. For compliance or security auditing, always use the API query rather than the Setup UI.
