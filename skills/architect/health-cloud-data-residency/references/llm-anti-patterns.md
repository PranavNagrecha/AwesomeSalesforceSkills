# LLM Anti-Patterns — Health Cloud Data Residency

Common mistakes AI coding assistants make when generating or advising on Health Cloud Data Residency.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Hyperforce Regional Selection Guarantees Complete Data Residency

**What the LLM generates:** "By selecting the EU Hyperforce region, all Health Cloud data will be stored and processed within the European Union, satisfying GDPR data residency requirements."

**Why it happens:** LLMs trained on marketing-adjacent documentation learn that Hyperforce's key value proposition is regional data storage. The nuance that transient processing for Einstein, analytics, and platform services may occur outside the primary region is less prominent in training data and is frequently omitted.

**Correct pattern:**

```
Hyperforce regional selection controls primary data-at-rest storage for core
Health Cloud objects and standard platform data. It does NOT guarantee:
- Einstein AI inference jobs remain in-region
- CRM Analytics / Health Cloud Intelligence pipelines are processed in-region
- MuleSoft integration traffic stays in-region
- All platform background services (DR replication, identity, support access)
  remain in-region

Each of the above must be separately evaluated and documented as a transient
processing exception or confirmed as in-region via current Salesforce
infrastructure documentation.
```

**Detection hint:** Any response that uses the phrase "all data will be stored and processed" in the context of Hyperforce regional selection, or that does not mention transient processing exceptions, is likely making this error.

---

## Anti-Pattern 2: Treating the HIPAA BAA as Covering All Salesforce Products in a Health Cloud Implementation

**What the LLM generates:** "Since you have the Salesforce HIPAA Business Associate Agreement in place, your Health Cloud implementation including Health Cloud Intelligence dashboards, MuleSoft EHR integration, and Marketing Cloud patient communications is fully covered."

**Why it happens:** LLMs generalise from the pattern "organisation has BAA with vendor → all vendor products are covered." The Salesforce HIPAA BAA is deliberately scoped to specific products, and the LLM's training data on BAA addendum requirements for specific products (HCI, MuleSoft, Marketing Cloud) is sparse compared to the general BAA concept.

**Correct pattern:**

```
HIPAA BAA Coverage Check — required for each feature:

Standard Salesforce HIPAA BAA covers:
  ✓ Core Health Cloud (EHR data model, care plans, patient timelines)
  ✓ Sales Cloud / Service Cloud standard features
  ✓ Standard platform features

Requires SEPARATE BAA addendum:
  ⚠ Health Cloud Intelligence / CRM Analytics
  ⚠ MuleSoft Anypoint Platform
  ⚠ Marketing Cloud (if PHI flows to Marketing Cloud)
  ⚠ Einstein AI features (verify current addendum scope per feature)

Each feature in the implementation must be mapped to its BAA status
before PHI is permitted to flow through it.
```

**Detection hint:** Any response that asserts a single BAA covers all Salesforce products without listing features and their specific coverage status, or that does not mention addenda requirements for HCI, MuleSoft, or Marketing Cloud.

---

## Anti-Pattern 3: Advising That Data Mask Automatically De-Identifies PHI in Sandboxes

**What the LLM generates:** "Enable Data Mask on your sandbox and it will automatically anonymize all sensitive patient data, making the sandbox safe to share with your development team."

**Why it happens:** Data Mask is marketed as a PHI de-identification tool for sandboxes, and LLMs pick up this framing. The critical detail — that Data Mask only masks fields explicitly configured in a mask profile, and that the default profile does not identify PHI fields — is an implementation nuance that is underrepresented in training data relative to the feature's general description.

**Correct pattern:**

```
Data Mask de-identifies only the fields explicitly listed in the mask profile.
Required steps:

1. Audit all PHI-containing fields:
   - Standard Health Cloud fields (HealthCloudGA__* namespace)
   - Custom fields added by the implementation
   - ContentDocument / ContentNote / ContentVersion bodies
   - Task.Description, EmailMessage.TextBody, FeedItem.Body
   - Any rich-text or long-text area fields used for clinical notes

2. Map each PHI field in the Data Mask profile to an appropriate
   masking type (random name, random date, nullify, pattern replace).

3. After sandbox creation + mask execution, spot-check masked records
   by opening actual records and files to verify no real PHI remains.

4. Update the mask profile whenever new fields are added to the org.
```

**Detection hint:** Any response that says Data Mask "automatically" or "by default" de-identifies PHI, or that does not require explicit field-by-field configuration and post-mask validation.

---

## Anti-Pattern 4: Conflating GDPR Data Residency with GDPR Article 9 Special-Category Obligations

**What the LLM generates:** "To comply with GDPR for your Health Cloud implementation, select the EU Hyperforce region. This ensures your data stays in the EU and satisfies GDPR requirements."

**Why it happens:** GDPR compliance for cloud services is most commonly discussed in terms of data transfer and regional storage. The additional obligations for special-category data under Article 9 — explicit consent, DPIA, DPO involvement, stricter legal basis requirements — are often not surfaced in the LLM's generalised GDPR guidance because they require understanding that health data triggers a higher-stringency regime.

**Correct pattern:**

```
GDPR compliance for Health Cloud requires addressing TWO distinct layers:

Layer 1 — Data Transfer/Residency (addressed by Hyperforce + DPA):
  - EU Hyperforce region for primary data storage
  - Salesforce Data Processing Addendum (DPA) executed
  - Standard Contractual Clauses or adequacy decision for any
    cross-border transfers

Layer 2 — Article 9 Special-Category Obligations (additional requirements):
  - Health data = special-category personal data → stricter rules apply
  - Explicit consent (Article 9(2)(a)) OR another Article 9(2) exemption
    required as legal basis (legitimate interest does NOT apply)
  - Data Protection Impact Assessment (DPIA) mandatory before deployment
  - Data Protection Officer (DPO) sign-off required if processing at scale
  - Data minimisation: Health Cloud default data model is expansive;
    field-level security must be tightened to minimum necessary
  - Purpose limitation: document each processing purpose explicitly

Both layers must be satisfied. Addressing Layer 1 alone does not satisfy
Article 9 obligations.
```

**Detection hint:** Any response that addresses GDPR for Health Cloud only through Hyperforce regional selection and a DPA, without mentioning Article 9 special-category data obligations, explicit consent/legal basis requirements, or DPIA requirements.

---

## Anti-Pattern 5: Recommending Full Sandbox Creation from Health Cloud Production Without De-Identification Gating

**What the LLM generates:** "Create a full sandbox copy of your production org for development and testing purposes. This gives your team access to real data for realistic testing scenarios."

**Why it happens:** "Use real data for realistic testing" is common general software development advice. LLMs do not consistently apply the HIPAA/GDPR overlay that makes this advice dangerous in a Health Cloud context. The HIPAA minimum necessary standard and GDPR data minimisation principle both prohibit exposing real PHI to development or QA teams unless those team members are covered by the BAA and the exposure is necessary.

**Correct pattern:**

```
Health Cloud sandbox creation from production requires a mandatory
de-identification gate before developer/tester access is granted:

Step 1: Create the full sandbox (PHI is present at this point)
Step 2: Apply Data Mask with an explicit, validated PHI mask profile
         — do NOT grant access between Steps 1 and 2
Step 3: Spot-check masked records and attached files for residual PHI
Step 4: Grant developer/QA access only after Step 3 confirms clean state
Step 5: Ensure only team members covered by the HIPAA BAA have access
         to the sandbox during Steps 1–3

For offshore or non-BAA-covered personnel:
  → Access to any Health Cloud sandbox is permitted ONLY after
    full de-identification is confirmed by a BAA-covered team member.
  → Document the de-identification verification as a compliance record.

Alternatives to consider:
  - Partial sandbox with synthetic/anonymized data from the start
  - Developer sandboxes with fully synthetic data (no production copy)
  - Data Mask applied immediately post-creation before any login
```

**Detection hint:** Any response that recommends creating a full sandbox from a Health Cloud production org without immediately pairing it with explicit PHI de-identification gating steps, or that frames real-data testing as beneficial without addressing the HIPAA/GDPR constraint.

---

## Anti-Pattern 6: Assuming Australia My Health Records Act Compliance Follows Automatically from Hyperforce AU Region Selection

**What the LLM generates:** "For your Australian healthcare client, select the Salesforce Australia (Sydney) Hyperforce region. This will ensure compliance with Australian health data regulations including the My Health Records Act."

**Why it happens:** The logical inference "Australian data law → Australian region = compliant" is plausible but incorrect for the My Health Records Act, which has specific cross-border disclosure restrictions and registered system operator obligations that are not automatically satisfied by regional primary storage. LLMs lack the specific statutory knowledge of the My Health Records Act 2012 and default to the general pattern.

**Correct pattern:**

```
My Health Records Act 2012 compliance requires:

1. Salesforce's Hyperforce AU region for primary data storage — NECESSARY
   but NOT SUFFICIENT alone.

2. Review of Hyperforce Infrastructure Agreement for AU — identify every
   documented cross-border processing exception and assess each against
   the Act's definition of "disclosure."

3. Einstein and analytics features — each must be evaluated for whether
   inference or pipeline processing crosses the AU border. Features that
   do are not permitted for My Health Record data until:
   (a) Salesforce confirms AU-region processing, OR
   (b) Data is de-identified before reaching the feature

4. Salesforce's formal compliance position — request from the Salesforce
   account team any available letters of assurance or compliance
   certifications specific to My Health Records Act obligations.

5. Legal review — engage an Australian health law specialist to confirm
   that the documented architecture satisfies the Act's requirements,
   including the cross-border disclosure restriction and any registered
   system operator conditions specific to the client's registration.
```

**Detection hint:** Any response that asserts My Health Records Act compliance based solely on Hyperforce AU region selection, without referencing cross-border processing exceptions, transient processing evaluation, or the need for formal legal confirmation of compliance.
