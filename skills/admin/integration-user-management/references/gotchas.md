# Gotchas — Integration User Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: MFA Waiver Is Not Inherited — New Integration Users Created After Enforcement Are Blocked

**What happens:** When org-wide MFA enforcement is enabled, all users including integration users are subject to MFA. Existing integration users that already had the exemption retain it. However, any new integration user created after MFA enforcement is enabled does NOT automatically receive the MFA User Exemption. On first API login attempt, the user receives an authentication failure even though the profile is correct and the password is valid.

**When it occurs:** Any time a new integration user is provisioned in an org that has org-wide MFA enforcement active. This is particularly common during org migration projects, onboarding of new integrations post-hardening, or cloning an integration user without copying permission set assignments.

**How to avoid:** Include MFA User Exemption assignment as a mandatory step in the integration user provisioning checklist. Use a dedicated "Integration MFA Waiver" permission set and assign it to every new integration user. Verify via Login History immediately after provisioning — do not wait for the first production failure.

---

## Gotcha 2: System Administrator Profile Silently Removes the API-Only Restriction

**What happens:** Assigning the System Administrator profile (or any profile cloned from System Administrator) to an integration user silently removes the API-only enforcement. The integration user can now log in interactively via the browser, Salesforce mobile, and Lightning Experience — in addition to the API. This is not surfaced as an error or warning. The integration continues to function, making this easy to miss.

**When it occurs:** When a practitioner wants to "quickly unblock" an integration by giving it admin access, or when an admin clones a profile from System Administrator thinking they can restrict permissions later. It also occurs when an integration user's profile is changed during a troubleshooting session and not reverted.

**How to avoid:** Always use the Minimum Access - API Only Integrations profile for integration users. Do not clone admin profiles for integration use. Periodically audit integration user profiles via SOQL: `SELECT Username, Profile.Name FROM User WHERE UserType = 'Standard' AND Profile.Name != 'Minimum Access - API Only Integrations' AND IsActive = TRUE` — flag any integration-named users on non-API-only profiles.

---

## Gotcha 3: Login History UI Cap Causes Audit Gaps for High-Volume Integrations

**What happens:** The Setup > Login History UI displays a maximum of 20,000 records within a 6-month rolling window. High-volume integrations that make many API calls per hour can fill this window quickly, pushing older login records out of the visible range. This means an audit performed after the fact may not surface failed login attempts that occurred before the window was exhausted.

**When it occurs:** In orgs with multiple active integrations, high-frequency polling integrations, or integrations performing batch operations. The problem is invisible until a security team requests a full login history report and discovers the gap.

**How to avoid:** Do not rely solely on the Login History UI for integration user auditing. Query the `LoginHistory` object via SOQL directly or via the Reports tab to export data before it ages out. Schedule a weekly report export to an external system or append LoginHistory records to an external log store. Consider using Event Monitoring (if licensed) for durable, queryable login event data that is not subject to the 20,000-record UI cap.

---

## Gotcha 4: Permission Set License Mismatch Prevents Object Permission Assignment

**What happens:** When creating a permission set to assign to an integration user (Salesforce Integration license), if the permission set is not assigned the **Salesforce API Integration** permission set license (PSL), the permission set editor may not display the expected object permissions or may silently fail to save certain permission configurations. The permission set appears to exist but the integration user cannot access the expected objects.

**When it occurs:** When a practitioner creates a generic permission set without setting the correct PSL, then assigns it to an integration user. Also occurs when copying permission sets originally created for standard Salesforce license users and assigning them to integration license users without updating the PSL.

**How to avoid:** When creating any permission set for an integration user, set the Permission Set License to "Salesforce API Integration" before adding any object or field permissions. Verify via SOQL: `SELECT Id, Label, LicenseId FROM PermissionSet WHERE Label = '<your permission set name>'` — confirm the LicenseId corresponds to the Salesforce API Integration PSL.

---

## Gotcha 5: Connected App "Run As" User Must Be the Integration User, Not an Admin

**What happens:** When configuring a Connected App for OAuth client credentials flow, the "Run As" field determines the identity Salesforce uses when executing API calls authenticated via that connected app. If "Run As" is set to a System Administrator or any non-integration user, the API calls execute with that user's permissions — not the integration user's permission sets. The integration appears to work but is running with elevated privileges. If "Run As" is later corrected to the integration user, the integration may suddenly fail due to missing permissions that were silently provided by the admin account.

**When it occurs:** During initial Connected App setup when the person configuring the app uses their own account or a generic admin account in the "Run As" field as a shortcut. The mismatch is not surfaced as an error.

**How to avoid:** Always set the Connected App "Run As" field to the dedicated integration user. Validate after setup by checking Login History — the UserId in successful OAuth login records should match the integration user's Id, not any admin user's Id.
