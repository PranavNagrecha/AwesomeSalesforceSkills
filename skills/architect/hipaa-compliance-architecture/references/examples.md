# Examples — HIPAA Compliance Architecture

## Example 1: Architecture Review for a Health Cloud Org Storing PHI — BAA Scope Validation

**Context:** A regional health system is launching a Salesforce Health Cloud implementation to manage patient care coordination. The implementation team has enabled Health Cloud, installed a third-party e-signature AppExchange package, activated Einstein Next Best Action for care team recommendations, and plans to use standard Chatter for clinical team communication. The customer has a signed BAA with Salesforce but has not reviewed its covered product list.

**Problem:** The team assumes that because they have a BAA with Salesforce, all features they activate in their org are HIPAA-covered. Without a BAA scope validation step, PHI will flow into services that are not covered — creating a reportable breach exposure.

**Solution:**

Step 1 — Obtain the executed BAA from the Salesforce account team and extract the covered product list.

Step 2 — Build the BAA scope map:

```
| Product / Service               | BAA Covered? | Notes                                          |
|---------------------------------|--------------|------------------------------------------------|
| Health Cloud                    | Yes          | Explicitly listed in BAA                       |
| Sales/Service Cloud (base)      | Yes          | Covered under platform                         |
| Shield Platform Encryption      | Yes          | Shield add-on is BAA-covered when licensed     |
| Shield Field Audit Trail        | Yes          | BAA-covered                                    |
| Event Monitoring                | Yes          | BAA-covered                                    |
| Standard Chatter                | NO           | Not covered — PHI must not be posted here      |
| Einstein Next Best Action       | Review       | Verify current BAA version; may be excluded    |
| [ISV] E-signature Package       | NO           | ISV manages own data — requires ISV BAA addendum |
| Sandbox (Developer/Partial)     | Review       | Confirm Sandbox coverage in BAA version        |
```

Step 3 — For the e-signature ISV: contact the vendor and request a signed BAA addendum. Until received, configure validation rules to prevent PHI fields from being passed to the package's integration endpoints.

Step 4 — For standard Chatter: document the gap as a risk item. Redirect clinical team communication to a BAA-covered channel (e.g., a configured Experience Cloud community or a HIPAA-covered messaging integration). Add a Salesforce Org Health Check review item.

Step 5 — For Einstein Next Best Action: review the current Salesforce HIPAA help article (`help.salesforce.com/s/articleView?id=sf.compliance_hipaa.htm`) to confirm current coverage status. If not listed, do not use PHI as recommendation model input until confirmed.

**Why it works:** BAA coverage is contractual and product-specific, not infrastructure-wide. The scope validation step forces an explicit coverage decision for every service before PHI is introduced, creating an auditable record for the covered entity's risk assessment.

---

## Example 2: Shield Platform Encryption Field Selection Strategy for PHI Fields

**Context:** A payer organization has Shield Platform Encryption licensed and wants to encrypt all PHI in their Salesforce org. A developer proposes applying probabilistic encryption to every field flagged as PHI — including the patient's First Name, Last Name, Date of Birth, and Member ID fields that are used in SOQL WHERE clauses, list views, and a formula field that concatenates name and member ID for display.

**Problem:** Applying probabilistic encryption to searchable and formula-referenced fields will silently break SOQL exact-match queries (range queries and LIKE fail entirely), render the formula field blank, and break list view sorting — all without compile-time errors. The org will appear to function but return incorrect data.

**Solution:**

Step 1 — Conduct functional dependency analysis for each candidate PHI field before assigning an encryption scheme:

```
| Field                          | Used in SOQL WHERE? | Used in Formula? | Used in Sorting? | Encryption Scheme     |
|-------------------------------|---------------------|------------------|------------------|-----------------------|
| Contact.FirstName              | Yes (exact match)   | Yes              | Yes              | DETERMINISTIC         |
| Contact.LastName               | Yes (exact match)   | Yes              | Yes              | DETERMINISTIC         |
| Contact.Birthdate              | Yes (range query)   | No               | Yes              | DO NOT ENCRYPT*       |
| Contact.SSN__c (custom)        | No                  | No               | No               | PROBABILISTIC         |
| Contact.MemberID__c            | Yes (exact match)   | Yes              | No               | DETERMINISTIC         |
| Contact.ClinicalNotes__c       | No                  | No               | No               | PROBABILISTIC         |
| Contact.HomePhone              | Yes (exact match)   | No               | No               | DETERMINISTIC         |
```

*Birthdate: SPE does not support range queries (>, <, BETWEEN) on encrypted fields. If range queries are required, encrypt at the application layer or implement a de-identified bucketing strategy (e.g., age range field). Evaluate whether Birthdate must be stored in a searchable field vs. a display-only field.

Step 2 — For the formula field that concatenates FirstName + MemberID: deterministic encryption on source fields allows the formula to function only if the formula field itself is also designated as encrypted or is a non-encrypted display field. Verify formula behavior in a Shield-enabled Sandbox before production.

Step 3 — Document the encryption policy matrix in the PHI field inventory artifact. Include the justification for deterministic vs. probabilistic assignments.

Step 4 — In a Sandbox with Shield enabled, validate each list view, report, and SOQL query that references PHI fields. Confirm encryption does not silently return empty results.

Step 5 — Plan the production SPE enablement during a maintenance window. Monitor the bulk re-encryption job progress via `Setup > Platform Encryption > Encryption Statistics`.

**Why it works:** Deterministic encryption preserves exact-match SOQL query capability at the cost of slightly reduced theoretical security (two identical plaintext values produce the same ciphertext, enabling inference attacks). For fields that must be searchable or used in formulas, deterministic encryption is the correct tradeoff. For fields that are stored-only with no query requirements, probabilistic encryption provides stronger protection. The field-by-field analysis prevents the silent data corruption that results from applying probabilistic encryption to searchable fields.

---

## Anti-Pattern: Treating Shield Enablement as Full HIPAA Compliance

**What practitioners do:** An implementation team enables Shield Platform Encryption, points to the Shield license in their documentation, and tells the covered entity "we've implemented HIPAA technical safeguards — you're compliant." The architecture review stops at Shield.

**What goes wrong:** Shield covers encryption at rest (SPE), extended audit trail (FAT), and event logging (Event Monitoring). HIPAA technical safeguards also require: unique user identification, emergency access procedures, automatic session logoff, and transmission security. HIPAA administrative safeguards require: risk analysis, workforce training, sanction policies, access authorization procedures, and incident response planning. Shield does not address any administrative safeguards and covers only a subset of technical safeguards. A HIPAA audit will identify these gaps as findings, and the covered entity — not Salesforce — bears the compliance obligation.

**Correct approach:** Produce a HIPAA Security Rule safeguard matrix that maps every required safeguard (administrative, physical, technical) to the specific Salesforce control or organizational policy that satisfies it. Shield controls are documented in the technical safeguard column. Administrative and remaining technical safeguard gaps require org configuration (MFA enforcement, session timeout policy, access provisioning workflow) and covered entity policy documentation. Present the complete matrix — not just the Shield components — to the covered entity's compliance team.
