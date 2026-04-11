# LLM Anti-Patterns — Patient Engagement Requirements

Common mistakes AI coding assistants make when generating or advising on patient engagement requirements.

## Anti-Pattern 1: Assuming Patient Portal Is Included in Base Health Cloud

**What the LLM generates:** Architecture designs and implementation steps for a patient-facing portal that assume Health Cloud includes patient portal capability, without noting that Experience Cloud for Health Cloud is a separately licensed add-on.

**Why it happens:** Health Cloud documentation extensively describes patient portal features. LLMs present these features as part of Health Cloud without knowing the product boundary between Health Cloud (care coordinator/clinician tool) and Experience Cloud for Health Cloud (patient-facing portal, separate add-on).

**Correct pattern:**
Patient portal functionality requires the Experience Cloud for Health Cloud add-on SKU with per-user licensing. This must be explicitly included in the contract. Confirm the add-on is licensed before scoping any patient-facing portal features.

**Detection hint:** If the patient portal implementation plan does not mention "Experience Cloud for Health Cloud" as a separate licensed add-on, the license dependency is missing.

---

## Anti-Pattern 2: Including No-Show Prediction Without CRM Analytics License

**What the LLM generates:** Intelligent Appointment Management requirements that include no-show risk prediction as a standard feature, without noting the CRM Analytics license dependency.

**Why it happens:** No-show prediction is prominently featured in IAM product marketing and documentation. LLMs present it as a native IAM feature without knowing that the AI/ML prediction layer requires a separately licensed CRM Analytics add-on.

**Correct pattern:**
IAM core appointment scheduling works without CRM Analytics. No-show prediction specifically requires CRM Analytics (formerly Tableau CRM) as a separate license. When scoping IAM, explicitly separate core scheduling from predictive analytics requirements and confirm the CRM Analytics license if prediction is needed.

**Detection hint:** If IAM requirements include no-show prediction without mentioning CRM Analytics as a license requirement, the dependency is missing.

---

## Anti-Pattern 3: Assuming OmniStudio Is Auto-Installed with Health Cloud

**What the LLM generates:** Health assessment configuration steps that assume OmniStudio is ready to use immediately after Health Cloud is licensed, without noting that the managed package must be separately installed.

**Why it happens:** OmniStudio is licensed as part of Health Cloud. LLMs conflate "licensed" with "installed and active." The managed package installation step is a deployment action, not a license activation.

**Correct pattern:**
OmniStudio must be explicitly installed as a managed package (via AppExchange or managed package installer) even if licensed within Health Cloud. Discovery Framework must be installed separately after OmniStudio. Verify installation status in Setup > Installed Packages before scoping any OmniScript-based assessment work.

**Detection hint:** If assessment implementation steps begin with OmniStudio configuration without verifying the managed package is installed, the installation prerequisite is missing.

---

## Anti-Pattern 4: Using Standard Chatter for Patient-Clinician Messaging

**What the LLM generates:** Patient messaging solutions that route clinical communications (care instructions, assessment results) through Salesforce Chatter because it is built-in and available.

**Why it happens:** Chatter is the default Salesforce collaboration tool with extensive training data. LLMs recommend it for internal messaging without knowing that standard Chatter is not covered by the default Salesforce BAA for PHI.

**Correct pattern:**
Patient-clinician clinical communications (appointment details, care instructions, PHI-containing messages) must use HIPAA-covered channels. Use Messaging for In-App and Web with the Messaging User permission set. Verify BAA coverage for the specific messaging channel. Do not use standard Chatter for PHI-containing clinical communications.

**Detection hint:** If the patient messaging solution uses standard Chatter or generic email without BAA coverage verification, the HIPAA channel compliance requirement is missing.

---

## Anti-Pattern 5: Designing Portal Features Without Per-User License Planning

**What the LLM generates:** Patient portal implementations that do not account for per-user Experience Cloud for Health Cloud license assignment, assuming a single org-level license covers all patient users.

**Why it happens:** Experience Cloud licensing models (per-user vs. login vs. member-based) are complex. LLMs often present portal implementation steps without detailing per-user license assignment requirements, particularly for patient-facing portals where each patient is an Experience Cloud user.

**Correct pattern:**
Experience Cloud for Health Cloud uses per-user licensing — each patient portal user requires an Experience Cloud for Health Cloud license assigned via permission set. Estimate the patient user population size for licensing cost planning. Factor per-user license costs into the total project budget. Plan the permission set assignment process for patient onboarding.

**Detection hint:** If the portal design does not include per-user license assignment planning and cost estimation, the per-user licensing requirement has been overlooked.
