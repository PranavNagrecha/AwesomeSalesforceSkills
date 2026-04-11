# LLM Anti-Patterns — HIPAA Compliance Architecture

Common mistakes AI coding assistants make when generating or advising on HIPAA compliance architecture in Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Shield Platform Encryption as the Only Required HIPAA Technical Safeguard

**What the LLM generates:** "To achieve HIPAA compliance on Salesforce, enable Shield Platform Encryption on all PHI fields. Once SPE is enabled, your technical safeguards requirement is satisfied."

**Why it happens:** LLMs associate "HIPAA + Salesforce" primarily with Shield and encryption, which dominates training data on the topic. The full HIPAA Security Rule technical safeguard set — unique user identification, emergency access procedures, automatic logoff, encryption, and transmission security — is less prominent in training examples than Shield marketing content.

**Correct pattern:**

```
Shield Platform Encryption addresses:
  - Encryption at rest (45 CFR §164.312(a)(2)(iv)) — YES, SPE covers this
  - Transmission encryption (§164.312(e)(2)(ii)) — partially (TLS in transit is platform-default)

HIPAA technical safeguards also require (Shield does NOT address these):
  - Unique user identification (§164.312(a)(2)(i)) — MFA + named user accounts
  - Emergency access procedure (§164.312(a)(2)(ii)) — documented break-glass process
  - Automatic logoff (§164.312(a)(2)(iii)) — session timeout configuration
  - Audit controls (§164.312(b)) — Field Audit Trail + Event Monitoring (separate Shield components)

Administrative safeguards (not covered by any Shield component):
  - Risk analysis (§164.308(a)(1))
  - Workforce training (§164.308(a)(5))
  - Incident response (§164.308(a)(6))
  - Access management (§164.308(a)(4))
```

**Detection hint:** Any response that references only Shield or only encryption when asked about "HIPAA compliance on Salesforce" is missing the non-Shield requirements. Look for absence of MFA, session timeout, risk assessment, or workforce training discussion.

---

## Anti-Pattern 2: Assuming Standard Chatter Is Covered by the Salesforce BAA

**What the LLM generates:** "You can use Chatter to allow care team members to collaborate on patient cases. Since you have a BAA with Salesforce, Chatter communication is covered."

**Why it happens:** Chatter is a core Salesforce platform feature that feels foundational. LLMs generalize "Salesforce BAA" to cover the entire platform rather than the specific product list in the executed agreement. Chatter's exclusion from BAA coverage is a nuance not prominently featured in most training corpus discussions of Salesforce HIPAA.

**Correct pattern:**

```
Standard Chatter is NOT listed in the Salesforce HIPAA BAA covered product list 
as of current Salesforce published guidance.

Recommended alternatives for BAA-covered clinical team communication:
  - Experience Cloud community (verify Experience Cloud is listed in your executed BAA)
  - A HIPAA-covered third-party messaging integration (with its own ISV BAA addendum)
  - Email-to-Case or Case Comments through Service Cloud (BAA-covered)

Always verify the current covered product list at:
  help.salesforce.com/s/articleView?id=sf.compliance_hipaa.htm
before recommending any Salesforce feature for PHI-bearing workflows.
```

**Detection hint:** Any response recommending Chatter for clinical team communication in a HIPAA context without first verifying BAA coverage should be flagged. Look for phrases like "Chatter is part of the platform so it's covered."

---

## Anti-Pattern 3: Skipping the BAA Execution Step Before Recommending PHI Storage Architecture

**What the LLM generates:** "Here is the Health Cloud data model for storing patient PHI. Configure these objects and fields, enable Shield encryption, and you are ready to store patient data."

**Why it happens:** LLMs are trained on technical implementation guides that focus on configuration steps. The legal prerequisite — BAA execution — is a business/legal process not a technical one, so it is underrepresented in technical training content and tends to be omitted from architecture recommendations.

**Correct pattern:**

```
MANDATORY PREREQUISITE: Before any PHI architecture work proceeds:

1. Confirm the BAA with Salesforce has been fully executed (signed by both parties).
2. Obtain the signed BAA document and extract the covered product list.
3. Verify every product in the proposed architecture is listed in the BAA.

No PHI may be stored in Salesforce until step 1 is complete.
This is a legal requirement, not a best practice — it is the foundation of HIPAA BA compliance.

Only after BAA confirmation: proceed with technical architecture design.
```

**Detection hint:** Any architecture recommendation that begins with data model or Shield configuration without a BAA validation step is missing the foundational prerequisite. Look for absence of the word "BAA" or "Business Associate Agreement" in the opening steps.

---

## Anti-Pattern 4: Treating Shield as a Standard Feature Included in All Editions

**What the LLM generates:** "Enable Shield Platform Encryption in your org by going to Setup > Platform Encryption. You'll also want to turn on Field Audit Trail for the 10-year retention."

**Why it happens:** LLMs present Shield as a setup step rather than a separately licensed product. Training data on Shield implementation focuses on the configuration procedure, not on licensing prerequisites. The paid add-on requirement is often not stated in technical how-to content.

**Correct pattern:**

```
Shield Platform Encryption, Field Audit Trail, and Event Monitoring are 
paid add-ons that must be separately licensed and contracted.

They are NOT included in:
  - Salesforce Enterprise Edition
  - Salesforce Unlimited Edition
  - Health Cloud (any edition)
  - Any other standard Salesforce edition

Before recommending Shield controls, confirm licensing:
  Setup > Company Information > Permission Set Licenses
  Look for: Shield Platform Encryption User, Shield Event Monitoring User,
            Shield Field Audit Trail User

If Shield is not licensed, document the gap and evaluate:
  - Classic Encryption (very limited — custom text fields only, 175 char max)
  - Risk acceptance with the covered entity's compliance officer
  - Contract amendment to add Shield
```

**Detection hint:** Any response that walks through Shield configuration without first confirming the Shield license is present is skipping a critical prerequisite. Look for absence of any licensing verification step.

---

## Anti-Pattern 5: Recommending Uncovered Salesforce Services for PHI Storage

**What the LLM generates:** "Store patient documents using Salesforce Files (Content). You can also use Salesforce Data Cloud to unify patient profiles across your systems."

**Why it happens:** LLMs recommend Salesforce features appropriate to the use case (document storage → Files, data unification → Data Cloud) without applying a BAA coverage filter. The BAA coverage status of specific Salesforce products (Files/Content, Data Cloud, specific Einstein services) is not consistently stated in the training data associated with feature recommendation tasks.

**Correct pattern:**

```
Before recommending any Salesforce feature for PHI storage or processing:

1. Check whether the feature/product is listed in the executed BAA.
2. For Salesforce Files/Content: verify BAA coverage — content stored via Files 
   may be covered under the platform BAA, but confirm explicitly.
3. For Data Cloud (formerly Customer Data Platform): review current BAA coverage 
   status. Data Cloud is a separate product with its own data processing terms.
4. For any AI/Einstein feature: review the current BAA coverage list — 
   Einstein features vary in BAA inclusion and this changes with releases.

Rule: if a product is not explicitly listed in the BAA, treat it as uncovered
and do not use it to store or process PHI until coverage is confirmed.
```

**Detection hint:** Any response recommending Data Cloud, Einstein, Slack, or newer Salesforce platform additions for PHI handling without a BAA verification step is a potential compliance risk. Products added to Salesforce after the BAA was signed may not be covered by the existing agreement.

---

## Anti-Pattern 6: Applying Probabilistic SPE to Fields Used in SOQL Queries

**What the LLM generates:** "For maximum security, apply probabilistic encryption to all PHI fields including Name, Email, Phone, MemberID, and DateOfBirth."

**Why it happens:** "More encryption = more secure" is a reasonable heuristic that LLMs apply without understanding the SPE functional constraint: probabilistic encryption makes fields unsearchable via SOQL and unusable in formulas, list views, and workflows. The functional consequences are silent — queries return no results without an error.

**Correct pattern:**

```
SPE Encryption Scheme Selection:

DETERMINISTIC (use when field is queried or referenced in formulas):
  - Fields used in SOQL WHERE clauses
  - Fields displayed in list views
  - Fields referenced in formula fields
  - Fields used as merge fields in templates
  Trade-off: same plaintext → same ciphertext (reduced theoretical security)

PROBABILISTIC (use for stored-only fields with no query requirements):
  - SSN, clinical notes, payment card numbers
  - Fields never used in SOQL filters or formulas
  Trade-off: SOQL WHERE queries return 0 results (silent failure)

FIELDS THAT CANNOT BE ENCRYPTED:
  - Fields used in SOQL ORDER BY
  - External IDs
  - Unique fields
  - Auto-number fields
  - Fields used in SOQL GROUP BY

Validate encryption scheme assignments in a Shield-enabled Sandbox 
before production deployment.
```

**Detection hint:** Any response recommending "probabilistic encryption for all PHI fields" without a query-dependency analysis is applying a blanket rule that will break SOQL-dependent functionality silently.
