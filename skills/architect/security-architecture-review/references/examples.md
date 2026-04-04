# Examples — Security Architecture Review

## Example 1: Pre-Go-Live Security Review for a Healthcare Org (HIPAA)

**Context:** A regional hospital network has built a patient intake and case management solution on Salesforce Service Cloud. The org holds Protected Health Information (PHI) including diagnosis codes, treatment notes, and insurance policy numbers. The delivery team is four weeks from go-live and a compliance officer has requested a security architecture review before cutover.

**Review execution:**

**Sharing model findings:**
- The `Case` object OWD was set to "Public Read Only" during initial configuration because the team "needed everyone to see cases." With PHI in case fields, this is a **Critical** finding. Remediation: change OWD to "Private," create role-hierarchy-based sharing rules for clinical staff, and confirm support agents have the correct role assignments before go-live.
- Three Apex trigger handlers on `Case` use `without sharing` with no documented reason. Code review showed one handler was processing billing data in a system context — legitimate. The other two had no reason. Both were refactored to `with sharing` before go-live.
- Experience Cloud site OWD for `Case` was not explicitly set; it defaulted to internal OWD of "Public Read Only." External patients were able to read all case fields via the portal. **Critical** finding — external OWD must be set to "Private" for the `Case` object.

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
- Five Apex classes using `without sharing` were reviewed. Three had legitimate system-context reasons (batch processing, trigger on insert before user context established). Two had no documented reason and were refactored.

**Shield assessment:**
- No HIPAA or FedRAMP requirement; bank account numbers stored in custom fields meet the "financial account numbers" criterion.
- Platform Encryption recommended for bank account number fields, SSN fields used in identity verification. Medium finding with a recommendation to evaluate Shield within the year.

**Outcome:** Ten findings — two Critical, four High, three Medium, one Low. Both Critical findings resolved within 72 hours. Review report delivered to compliance officer with evidence of remediation for cyber insurance renewal.
