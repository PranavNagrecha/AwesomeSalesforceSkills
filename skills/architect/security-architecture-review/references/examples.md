# Examples — Security Architecture Review

## Example 1: Pre-Go-Live Security Review for a Healthcare Org (HIPAA)

**Context:** A regional hospital network has built a patient intake and case management solution on Salesforce Service Cloud. The org holds Protected Health Information (PHI) including diagnosis codes, treatment notes, and insurance policy numbers. The delivery team is four weeks from go-live and a compliance officer has requested a security architecture review before cutover.

**Review execution:**

**Sharing model findings:**
- The `Case` object OWD was set to "Public Read Only" during initial configuration because the team "needed everyone to see cases." With PHI in case fields, this is a **Critical** finding. Remediation: change OWD to "Private," create role-hierarchy-based sharing rules for clinical staff, and confirm support agents have the correct role assignments before go-live.
- Three Apex trigger handlers on `Case` use `without sharing` with no documented reason. Code review showed one handler was processing billing data in a system context — legitimate. The other two had no reason. Both were refactored to `with sharing` before go-live.
- Experience Cloud site OWD for `Case` was not explicitly set; it defaulted to internal OWD of "Public Read Only." External patients were able to read all case fields via the portal. **Critical** finding — external OWD must be set to "Private" for the `Case` object. (Note 2026-10-03: per the Security Guide this happens in orgs created before Spring '20, whose external defaults were copied from the original internal defaults; newer orgs default external access to Private. Once the internal OWD is changed to Private, the external level cannot stay more permissive, so the fix above also closes the external gap.)

**FLS findings:**
- A bespoke `@AuraEnabled` Apex method used to render a patient summary component queried `Case` including diagnosis code fields and returned a raw `Case` sObject to the LWC. The class declared `with sharing` but performed no FLS check. Any authenticated user who could construct an Aura request could read diagnosis codes for cases they could not see through the UI. **Critical** finding — rewrote method using `WITH USER_MODE` query and field-level filtering.
- Integration user profile had "Modify All Data" system permission enabled. **High** finding — removed system permission, created a dedicated permission set with only the object/field access required for the HL7 integration.

**Shield assessment:**
- Org holds HIPAA-regulated PHI: all three Shield "Required" criteria met.
- Recommendation: Shield licensing is required. Prioritize Platform Encryption for diagnosis and insurance fields, and Event Monitoring for audit trail of data exports.

**Outcome:** Seven findings total — three Critical, two High, two Medium. All Critical findings were remediated before go-live. Shield licensing was approved and scheduled for the first post-go-live sprint.

---

## Example 2: Annual Security Review for a Financial Services Org (PCI-adjacent)

**Context:** A fintech company uses Salesforce to manage loan applications. The org holds income verification data and bank account details used for origination. The org is three years old with 12 developers and 200 internal users. An annual security architecture review is required by their cyber insurance policy.

**Review execution:**

**Connected App findings:**
- A Connected App used for a legacy data warehouse sync had "Relax IP restrictions" enabled and OAuth scope set to `full`. The app had not been accessed in 180 days according to login history. **High** finding — the app's scope could not be narrowed without testing impact on the warehouse system, so the app was deactivated pending validation.
- Two Connected Apps had refresh tokens configured to never expire. Combined with IP relaxation, this meant a stolen refresh token would provide permanent, unrestricted access. **Critical** finding — token lifetime was set to eight hours for both apps, matching session timeout policy.
- A third-party DocuSign Connected App had `api` scope when only `signature` scope was required. Narrowed to `signature` scope. **Medium** finding.

**Apex security findings:**
- Dynamic SOQL found in a legacy LoanApplicationController that concatenated the status filter from a picklist value passed through the Aura component. While picklist values are constrained in the UI, direct API calls can supply arbitrary strings. **High** finding — rewritten to use a bind variable.
- Five Apex classes using `without sharing` were reviewed. Three had legitimate system-context reasons (batch processing, and a trigger handler that has to roll up to parent records the running user cannot see). Two had no documented reason and were refactored.

**Shield assessment:**
- No HIPAA or FedRAMP requirement; bank account numbers stored in custom fields meet the "financial account numbers" criterion.
- Platform Encryption recommended for bank account number fields, SSN fields used in identity verification. Medium finding with a recommendation to evaluate Shield within the year.

**Outcome:** Ten findings — two Critical, four High, three Medium, one Low. Both Critical findings resolved within 72 hours. Review report delivered to compliance officer with evidence of remediation for cyber insurance renewal.

---

## Example 3: Evidence Queries and Findings Register for an Annual Review

**Context:** A Service Cloud org created in 2017 (before Spring '20) runs a customer Experience Cloud site with guest access. It has 380 Apex classes, 41 OAuth apps, and an auditor who wants 12 months of evidence. Shield is not licensed.

**Evidence queries.** Run as a user with View Setup and Configuration and Customize Application, and save each result with its run date. Object and field names come from the Object Reference (`PermissionSetAssignment`, `PermissionSet`, `OauthToken`, `SetupAuditTrail`, `ApexClass`).

Privileged permission holders. `PermissionSet` exposes one `Permissions<Name>` boolean per permission (Object Reference, `PermissionsPermissionName`); confirm the exact field names with a describe before relying on them:

```soql
SELECT Assignee.Username, Assignee.IsActive, PermissionSet.Name, PermissionSet.IsOwnedByProfile
FROM PermissionSetAssignment
WHERE PermissionSet.PermissionsModifyAllData = true
```

Dormant OAuth tokens (users with Customize Application see every user's tokens):

```soql
SELECT AppName, UserId, LastUsedDate, UseCount
FROM OauthToken
WHERE LastUsedDate < LAST_N_DAYS:90
```

Setup changes in the window Setup Audit Trail still holds (at least 180 days; export it on a schedule for the auditor's 12 months):

```soql
SELECT CreatedDate, CreatedById, Action, Section, Display, DelegateUser
FROM SetupAuditTrail
WHERE CreatedDate = LAST_N_DAYS:180
```

Apex classes by API version, to bucket sharing and access-mode findings (the 67.0 boundary flips undeclared behavior):

```soql
SELECT Name, ApiVersion, NamespacePrefix
FROM ApexClass
WHERE NamespacePrefix = null AND ApiVersion < 67.0
```

**Findings register (the decision record this skill produces):**

| ID | Domain | Finding | Evidence | Severity | Decision |
|---|---|---|---|---|---|
| SEC-01 | Sharing | `Account` and `Contact` external default is Public Read Only (org predates Spring '20) and the site has 6,000 customer users | Sharing Settings export | Critical | Set external defaults to Private; open access with sharing sets for the customer's own account (sharing sets not covered in the fetched Security Guide; UNVERIFIED 2026-10-03) |
| SEC-02 | Apex | 212 classes below API 67.0 with no sharing declaration; 9 of them are `@AuraEnabled` controllers used on the site | `ApexClass` query, code review | High | Add `with sharing` and `WITH USER_MODE` to the 9 site controllers first; schedule the rest by exposure |
| SEC-03 | Apex | Site profile component returns `User.Phone` and `User.Email` via Apex; personal-info visibility settings are not enforced in Apex | Code review | High | Apply the Apex Developer Guide's personal-information visibility pattern |
| SEC-04 | API | 14 OAuth apps unused for 90+ days, 2 with tokens set never to expire | `OauthToken` query | High | Revoke tokens and deactivate the 14; replacement integrations use external client apps (new connected apps are restricted as of Spring '26) |
| SEC-05 | Secrets | Payment gateway key stored in an unprotected hierarchy custom setting, readable by the guest profile | Custom setting definition | Critical | Move to a named credential with an external credential; rotate the key today |
| SEC-06 | Audit | Setup Audit Trail holds about 180 days; auditor needs 12 months | `SetupAuditTrail` query | Medium | Weekly export to the GRC store; this year's gap recorded as a known limitation |
| SEC-07 | Shield | Bank account numbers on `Contact` with no encryption at rest | Field inventory | Medium | Evaluate Shield Platform Encryption within the year |

**Why it works:** each finding cites a query or export a second reviewer can rerun, Apex findings are scored on the class's API version rather than the org release, and every remediation names a mechanism the org can create today (external client apps, named credentials, sharing sets).

