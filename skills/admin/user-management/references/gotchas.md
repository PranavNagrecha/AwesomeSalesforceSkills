# Gotchas — User Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Changing a User's License Clears the Profile Field

**What happens:** When you change a user's User License type (e.g., from Salesforce Platform to Salesforce), the Profile field is cleared and must be reselected. If you save without re-selecting a profile, the user receives an error and cannot log in.

**When it occurs:** Any time the User License field is changed on an existing user record. Salesforce enforces license-profile compatibility — profiles are linked to a specific license type, so a profile valid for Salesforce Platform is not valid for the full Salesforce license.

**How to avoid:** After changing the license, always scroll down to the Profile field and explicitly select a new compatible profile before saving. If the user is active, check their access immediately after the change by logging in as them (Setup → Login As) to confirm they can see the expected tabs and objects.

---

## Gotcha 2: Deactivating a User Does Not Remove Them from Queues or Active Approval Steps

**What happens:** After deactivation, the user remains as a member of any queue they belonged to. Cases and leads continue routing to those queues. Active approval process steps that required the deactivated user's approval become permanently stuck — the request can neither advance nor be resubmitted until an admin manually reassigns the approval actor.

**When it occurs:** Every time a user is deactivated without prior cleanup. Particularly impactful when the user was a solo approver on a business-critical process (expense reports, contracts, purchase orders).

**How to avoid:** Before deactivating:
1. Search all Approval Processes for the user as a designated approver
2. Query `ProcessInstanceWorkitem` for pending items assigned to this user
3. Remove the user from all queues (Setup → Queues)
4. Use the "Manage Users" data export or a SOQL query to find all records owned by the user and mass-reassign them
5. Freeze first while you complete this checklist — deactivate only after all items are resolved

---

## Gotcha 3: Login Hours Restrict New Logins but Do Not Terminate Existing Sessions

**What happens:** A user who is already logged in when the end-of-login-hours boundary occurs (e.g., 6 PM) is NOT automatically logged out. Their session remains fully active. The restriction only prevents new logins outside the allowed window.

**When it occurs:** Whenever Login Hours are configured on a profile with the expectation that this will enforce an end-of-day logout. Security teams who configure this setting often assume it acts like an automatic session timeout.

**How to avoid:** To enforce actual session termination at the hour boundary, also configure Setup → Session Settings → "Force logout on session timeout" and set an appropriate session timeout value. Alternatively, use a Named User MFA policy and require reauthentication at the start of each session. Login Hours alone are not sufficient for a hard session cutoff.

---

## Gotcha 4: Chatter Free Users Cannot Be Upgraded to Standard Licenses In-Place

**What happens:** A Chatter Free user who later needs full Salesforce access cannot simply have their license changed to Salesforce. You must deactivate (or delete) the Chatter Free user record and create a brand-new user record with the Salesforce license. This creates a gap in the user's activity history — their Chatter posts may reference the old user record.

**When it occurs:** When a contractor or external collaborator initially gets a Chatter Free account and is later hired full-time. Admins attempt to "upgrade" the license in-place and are blocked by the platform.

**How to avoid:** If there is any possibility a Chatter Free user will need CRM access in the future, provision a full Salesforce license from the start. If the cost is a concern, deactivate them using the full license (which stops consuming it) rather than provisioning Chatter Free. This preserves the user record and allows reactivation with the full license later without data loss.

---

## Gotcha 5: A User Without a Role Cannot See Other Users' Records Even If OWD Is Public Read/Write

**What happens:** A user with no role assigned can see all records when OWD is set to Public Read/Write, but in orgs where OWD is Private or Public Read Only, a user without a role cannot benefit from the role hierarchy — they see only records they own. This is counterintuitive because the user may have a profile with full object permissions.

**When it occurs:** Any time a new user is created without a role in an org where OWD is not Public Read/Write for important objects (Accounts, Opportunities, Cases). Managers who need to see their team's pipeline find that even with Modify All on Opportunities, they cannot navigate to the Opportunities of their direct reports.

**How to avoid:** During user provisioning, always check the org's OWD settings for the objects the user will work with. If OWD is Private or Public Read Only, assign a role. In orgs with strict private sharing, "no role" is equivalent to "sees only own records" for all role-hierarchy-enabled objects.
