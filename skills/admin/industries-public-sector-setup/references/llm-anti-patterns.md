# LLM Anti-Patterns — Industries Public Sector Setup

Common mistakes AI coding assistants make when generating or advising on Public Sector Solutions (PSS) configuration.

## Anti-Pattern 1: Recreating PSS objects as custom objects

**What the LLM generates:** A custom object called `License_Application__c` with fields like `Applicant__c`, `License_Type__c`, `Status__c`, and a custom approval process — because the model treats PSS as "generic case management."

**Why it happens:** Training data is heavy on standard CRM object design patterns and light on industry-cloud shipped objects. The model defaults to "build it from scratch" when it does not recognize the shipped objects.

**Correct pattern:**

```
Use the shipped LicenseApplication object. Add agency-specific fields
via extension, do NOT recreate the core object. Confirm with:
  sf sobject describe --sobject LicenseApplication
```

**Detection hint:** Any custom object with a name that mirrors a PSS shipped object (LicenseApplication, BenefitDisbursement, IndividualApplication, RegulatoryCode) is a red flag.

---

## Anti-Pattern 2: Hard-coding eligibility rules in Apex or Flow

**What the LLM generates:** A Flow or Apex class full of nested `if` statements evaluating income, household size, and residency to determine benefit eligibility.

**Why it happens:** LLMs reach for Flow/Apex because they are the well-known general-purpose decisioning tools. The Business Rules Engine (BRE) is an industry-cloud feature with less training data.

**Correct pattern:**

```
Model eligibility as a BRE expression set. Version it. Deploy it with
metadata. Shipped benefits OmniScripts call BRE directly — rolling
your own Flow bypasses the auditable engine the agency expects.
```

**Detection hint:** A Flow or Apex class named like `EvaluateEligibility` or `BenefitQualification` in a PSS org is almost always wrong.

---

## Anti-Pattern 3: Customizing shipped OmniScripts in place

**What the LLM generates:** Direct edits to the `IntakeLicenseApplication` OmniScript shipped with PSS, adding fields and branching.

**Why it happens:** LLMs treat OmniScripts like any metadata — forgetting that industry-cloud shipped assets get replaced on managed-package upgrade.

**Correct pattern:**

```
Clone the shipped OmniScript first (Save As new version with a new name),
then customize the clone. The original stays as the upgrade anchor.
```

**Detection hint:** An OmniScript name matching the shipped catalog (no agency prefix) with modified steps is a silent upgrade hazard.

---

## Anti-Pattern 4: Building citizen portals without guest-user hardening

**What the LLM generates:** "Create an Experience Cloud site, add a self-registration page, done."

**Why it happens:** The model knows Experience Cloud self-reg is a common pattern and does not apply the stricter guest-user rules that public-sector orgs require (FERPA, HIPAA, CJIS, state PII statutes).

**Correct pattern:**

```
Apply the Experience Cloud guest user hardening guide: tighten sharing,
disable guest record modification, lock down profile field-level security,
enable reCAPTCHA on self-reg, enable clickjack protection, turn on secure
guest user record access.
```

**Detection hint:** A PSS site deployment without explicit references to guest user sharing settings is underconfigured.

---

## Anti-Pattern 5: Skipping jurisdictional hierarchy and building flat sharing

**What the LLM generates:** A simple role hierarchy with one role per case team and OWDs set to Public Read/Write on most objects "for ease."

**Why it happens:** The LLM generalizes from typical B2B CRM designs where flat sharing is acceptable. Public sector is fundamentally jurisdictional.

**Correct pattern:**

```
Model the agency's statutory structure FIRST (state → region → local),
mirror it in the role hierarchy and Agency account hierarchies, and
set restrictive OWDs with criteria-based sharing on top. Retrofitting
this after data is loaded is a multi-day sharing-recalc outage.
```

**Detection hint:** A PSS implementation with Public Read/Write OWD on `Case`, `LicenseApplication`, or `BenefitDisbursement` is almost certainly non-compliant.
