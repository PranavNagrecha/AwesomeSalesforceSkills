# Gotchas — Health Cloud Consent Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Missing Default AuthorizationFormText Causes Silent Form Display Failure

**What happens:** The consent form component renders with no content — no text, no signature field, no consent options. The patient or enrollment staff sees a blank form area with no error message.

**When it occurs:** Whenever an AuthorizationForm has AuthorizationFormText records but none of them have IsDefault = true. This commonly happens when admins create multiple locale variants and forget to set the default flag, or when the default record is deactivated.

**How to avoid:** After creating or modifying AuthorizationFormText records, verify in Setup or SOQL that exactly one record per form has IsDefault = true. Query: `SELECT Id, IsDefault, Locale FROM AuthorizationFormText WHERE AuthorizationFormId = '[formId]'`. There should be exactly one record with IsDefault = true.

---

## Gotcha 2: AuthorizationFormConsent Status Values Are Picklist-Dependent

**What happens:** Custom consent status workflow breaks or form displays incorrectly when custom picklist values are added to AuthorizationFormConsent.Status without updating all downstream Flow and validation logic.

**When it occurs:** When an admin adds custom status values (e.g., "Pending Review", "Expired") to the Status picklist without reviewing all Flow decisions, validation rules, and Apex code that checks for specific status strings like "Signed" or "Seen".

**How to avoid:** Before adding custom Status values, audit all Flows, validation rules, and Apex that reference AuthorizationFormConsent.Status values. Plan for the full status lifecycle. In Flows, use formula comparisons rather than hardcoded strings where possible.

---

## Gotcha 3: Withdrawal Is a Status Update, Not a Record Delete

**What happens:** Deleting an AuthorizationFormConsent record when a patient withdraws consent destroys the HIPAA audit trail. The history of when consent was obtained and when it was revoked is permanently lost, creating a compliance gap.

**When it occurs:** When data cleanup scripts, bulk delete operations, or manual admin actions target AuthorizationFormConsent records as part of patient record archival or "cleanup." Also common when junior admins interpret withdrawal as "remove the consent."

**How to avoid:** Never include AuthorizationFormConsent in any data deletion or archival workflow. Withdrawal = Status update to "Withdrawn" or equivalent terminal value. Add explicit exclusion comments to any data cleanup scripts. Train all admins on this pattern.

---

## Gotcha 4: AuthorizationFormConsent Does Not Grant or Restrict PHI Record Access

**What happens:** Storing consent in AuthorizationFormConsent does not automatically restrict or grant sharing of PHI records. A patient who has not signed consent can still have their records accessed by any user with object-level access unless separate sharing rules are configured.

**When it occurs:** Implementations assume that creating the consent object hierarchy automatically enforces access control. Consent tracking and access control are separate concerns in Health Cloud.

**How to avoid:** Implement record-level sharing rules, OWD settings, and care team role-based sharing as the access control mechanism. AuthorizationFormConsent is a tracking/audit object — it documents that consent was obtained but does not enforce it technically. The enrollment workflow must explicitly check consent status before proceeding, typically via a Flow validation step.
