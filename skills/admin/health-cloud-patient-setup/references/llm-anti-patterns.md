# LLM Anti-Patterns — Health Cloud Patient Setup

Common mistakes AI coding assistants make when generating or advising on Health Cloud Patient Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Person Account Enablement with Patient Record Type Creation

**What the LLM generates:** A single-step instruction such as "enable Person Accounts to create Health Cloud patient records" or a setup guide that lists Person Account enablement as the final step, without mentioning the separate patient record type creation that must follow.

**Why it happens:** Training data contains many articles about Person Accounts as a standalone feature. LLMs conflate the general Person Account feature (an org-level setting) with the Health Cloud patient record type (a Health Cloud Setup action). The distinction is subtle but critical — they are sequential prerequisites, not synonyms.

**Correct pattern:**

```
Step 1: Enable Person Accounts (org-level, irreversible) — Setup > Account Settings
Step 2: Create Patient record type on Account — Object Manager > Account > Record Types
Step 3: Assign Health Cloud patient page layout to the Patient record type
Step 4: Assign Patient record type to appropriate profiles
Step 5: Verify in Health Cloud Setup that the patient record type is recognized
```

**Detection hint:** Any response that presents Person Account enablement as sufficient to create clinical patient records, without a separate step for Health Cloud patient record type creation, contains this anti-pattern.

---

## Anti-Pattern 2: Recommending Standard Contact Fields for Clinical Data

**What the LLM generates:** Advice to "add a Medications field to the Contact or Account object" or Apex code that stores diagnosis information in `Account.Description` or a custom `Account.CurrentDiagnoses__c` field, rather than using Health Cloud clinical objects.

**Why it happens:** LLMs default to standard Salesforce object customization patterns because they appear in far more training data than Health Cloud's specialized clinical object model. The path of least resistance for "store patient data" is adding fields to Account or Contact, which is correct in standard CRM but wrong in Health Cloud.

**Correct pattern:**

```
Medications     → EhrPatientMedication (lookup: Account)
Diagnoses       → PatientHealthCondition (lookup: Account)
Immunizations   → PatientImmunization (lookup: Account)
Procedures      → PatientMedicalProcedure (lookup: Account)
Care Diagnoses  → CareDiagnosis (lookup: CarePlan)
```

**Detection hint:** Any suggestion to store medication, diagnosis, immunization, or procedure data in custom Account or Contact fields, or in standard text/picklist fields on those objects, is this anti-pattern.

---

## Anti-Pattern 3: Using Lightning App Builder to Configure the Patient Card

**What the LLM generates:** Instructions to "open Lightning App Builder, drag the fields you want to show on the patient record page, and publish the page." Or code that adds fields to the record detail component of the patient page layout as a substitute for Patient Card configuration.

**Why it happens:** Lightning App Builder is the standard Salesforce UI customization tool. LLMs trained on general Salesforce documentation default to it for any record page customization. The Patient Card component has its own configuration path in Health Cloud Setup that is not well-represented in general Salesforce documentation.

**Correct pattern:**

```
Navigate to: Setup > Health Cloud > Patient Card Configuration
(NOT: App Builder > Patient Record Page > Edit > Add Fields)

In Patient Card Configuration:
- Select the card section (e.g., Medications, Conditions, Allergies)
- Add fields from the target clinical object
- Save (changes propagate without republishing the Lightning page)
```

**Detection hint:** Any response that directs the user to Lightning App Builder to configure what appears inside the Patient Card component contains this anti-pattern. Lightning App Builder is used to add or remove the Patient Card component from the page, not to configure the fields displayed inside it.

---

## Anti-Pattern 4: Treating Care Team Roles as Standard Salesforce Role Hierarchy Entries

**What the LLM generates:** Instructions to "go to Setup > Roles and add Nurse Practitioner as a role under the Clinician hierarchy node" or Apex that references `UserRole` to determine care team membership.

**Why it happens:** Salesforce's standard "roles" concept (used for OWD sharing and record visibility) is prominent in all Salesforce documentation. LLMs conflate "role" in the care team context with "role" in the Salesforce security model — they are entirely separate concepts with different configuration paths and different purposes.

**Correct pattern:**

```
Care team roles are NOT in Setup > Roles (the sharing/visibility hierarchy).

Care team roles are in: Setup > Health Cloud Settings > Care Team Roles
- Add role: Nurse Practitioner, Type: Clinical, Active: true
- These appear in the care team role picklist on patient records
- They have no impact on record visibility or OWD sharing
```

**Detection hint:** Any response that directs the user to Setup > Roles (the standard role hierarchy) to configure care team roles, or any code that uses `UserRole` objects to determine care team membership, contains this anti-pattern.

---

## Anti-Pattern 5: Marking Person Account Enablement as Reversible or Low-Risk

**What the LLM generates:** Statements like "you can always disable Person Accounts later if it doesn't work out" or "enabling Person Accounts is a simple toggle that only affects the accounts you designate as person accounts." Or a setup guide that omits the irreversibility warning entirely.

**Why it happens:** LLMs often soften risk language to avoid alarming users, and may have encountered low-quality documentation that downplayed the impact. Person Account enablement is one of the most consequential irreversible changes in Salesforce administration, and its full impact is not always foregrounded in general documentation.

**Correct pattern:**

```
WARNING: Person Account enablement is PERMANENT and ORG-WIDE.
- Cannot be reversed by the customer or by Salesforce Support.
- Affects ALL Account and Contact records, queries, triggers, and integrations.
- Must be tested in full sandbox with complete regression before production enablement.
- Requires explicit sign-off from all integration partners.
- Omitting this warning in any setup guide is a documentation defect.
```

**Detection hint:** Any response that omits the irreversibility of Person Account enablement, or implies it can be undone, or suggests it only affects "designated" accounts without warning about the org-wide impact, contains this anti-pattern.

---

## Anti-Pattern 6: Assuming Health Cloud Ships with Patient Record Types Pre-Configured

**What the LLM generates:** Setup instructions that say "after installing Health Cloud, patient record types are automatically available" or that skip the record type creation step entirely, leading practitioners to search for a non-existent "Patient" record type in Object Manager.

**Why it happens:** Managed packages often configure foundational objects during installation. LLMs may assume Health Cloud does the same for record types. In practice, Health Cloud installs the managed package, layouts, and permission sets, but the patient record type on the Account object must be created by the administrator — it is not auto-created.

**Correct pattern:**

```
After installing the Health Cloud package:
1. Person Accounts must be enabled (not done by package install)
2. Patient record type must be CREATED by the admin in Object Manager > Account > Record Types
   (It is NOT pre-created by the managed package install)
3. Health Cloud patient page layout (installed by package) must be ASSIGNED to the new record type
```

**Detection hint:** Any response that says patient record types are automatically available after Health Cloud installation, or that skips record type creation as a required post-installation step, contains this anti-pattern.
