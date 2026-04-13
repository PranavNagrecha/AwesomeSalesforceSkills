# Examples — Integration User Management

## Example 1: Setting Up a New Integration User for a MuleSoft ETL Pipeline

**Context:** A MuleSoft integration needs to read Accounts and Contacts and write to a custom object (Order__c) in a production Salesforce org. Org-wide MFA enforcement was enabled last quarter. The team wants to follow least-privilege and cannot use a named employee's credentials.

**Problem:** Without a dedicated integration user on the correct license and profile, the team either reuses an employee's account (a compliance risk) or uses an admin-cloned profile that grants far more access than needed and allows interactive login.

**Solution:**

```
1. Create user:
   - License: Salesforce Integration
   - Profile: Minimum Access - API Only Integrations
   - Username: mulesoft-etl@company.sf.prod (use a non-personal email convention)

2. Create Permission Set: "MuleSoft ETL Integration Access"
   - Permission Set License: Salesforce API Integration
   - Object permissions:
       Account: Read
       Contact: Read
       Order__c: Read, Create, Edit

3. Assign the permission set to the integration user.

4. Assign MFA User Exemption:
   - Navigate to: Setup > Users > [Integration User] > Permission Set Assignments
   - Assign a permission set that includes "Multi-Factor Authentication for API Logins" exemption
   - Document justification: "Server-to-server integration; interactive login not possible on this profile"

5. Configure Connected App for OAuth Client Credentials flow.
   - Set Run As: the integration user
   - Grant the connected app to the integration user

6. Verify in Setup > Login History:
   - Confirm LoginType = "OAuth 2.0"
   - Confirm Status = "Success"
   - Confirm SourceIp = known MuleSoft runtime IP
```

**Why it works:** The Minimum Access - API Only Integrations profile enforces the API-only restriction at the platform level. The targeted permission set ensures the integration can only touch the three objects it needs. The explicit MFA waiver prevents login failures after org-wide MFA enforcement. Using OAuth client credentials rather than username-password avoids credential rotation risk.

---

## Example 2: Diagnosing an Integration Outage After MFA Enforcement

**Context:** An org enables mandatory MFA enforcement as part of a security hardening project. The next morning, an existing Salesforce-to-ERP integration begins returning HTTP 400 / invalid_grant errors. The integration user was set up correctly before MFA was turned on.

**Problem:** The integration user was not granted the MFA User Exemption before MFA enforcement went live. MFA enforcement applies retroactively to all users, including integration users. The exemption must be explicitly assigned — it is not inherited from the org's previous MFA state, and it is not granted automatically to Salesforce Integration license users.

**Solution:**

```
1. Confirm the failure mode via LoginHistory SOQL:
   SELECT Id, UserId, LoginTime, Status, LoginType, Application, SourceIp
   FROM LoginHistory
   WHERE UserId = '<integration_user_id>'
   ORDER BY LoginTime DESC
   LIMIT 50

   Look for Status = "Failed" entries timestamped after MFA enforcement was activated.

2. Assign the MFA User Exemption:
   Option A — via User detail page:
     Setup > Users > [Integration User] > scroll to "Permissions" section
     Enable: "Multi-Factor Authentication for API Logins" exemption (if available as a user permission)

   Option B — via Permission Set (recommended for auditability):
     Create or use a dedicated "Integration MFA Waiver" permission set
     Enable: "Multi-Factor Authentication for API Logins" exemption in System Permissions
     Assign the permission set to the integration user

3. Retry the integration authentication.

4. Confirm recovery in Login History:
   Status = "Success" for new login attempts.

5. Document the exemption assignment in the project record with:
   - Date applied
   - Who approved
   - Business justification
   - Review date (recommended: annual)
```

**Why it works:** The MFA User Exemption grants the integration user the ability to authenticate via API without completing an MFA challenge. Because server-to-server integrations cannot perform interactive MFA, this exemption is required — but it must be explicitly granted. Tracking it via a dedicated permission set makes it auditable and easy to revoke or review.

---

## Anti-Pattern: Using the System Administrator Profile for Integration Users

**What practitioners do:** To avoid figuring out which specific permissions an integration needs, practitioners clone the System Administrator profile and assign it to the integration user. This "works" immediately because the admin profile has access to everything.

**What goes wrong:** The System Administrator profile does not have the "API Only" flag set. This means the integration user can now authenticate via the Salesforce UI, browser, and mobile app — they are a fully interactive admin-level account with a service username. This violates least privilege, creates a significant blast-radius risk if the credential is compromised, and will fail security audits. Additionally, if the org is subject to MFA enforcement, an admin-profile user without the API Only flag is treated as an interactive user and may be required to complete MFA in unexpected ways.

**Correct approach:** Always use the Minimum Access - API Only Integrations profile for integration users. Layer on exactly the permissions needed via targeted permission sets. If the list of required permissions is unclear, start with read-only access to the required objects and expand after testing.
