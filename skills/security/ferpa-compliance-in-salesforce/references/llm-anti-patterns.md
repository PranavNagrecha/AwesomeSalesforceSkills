# LLM Anti-Patterns — FERPA Compliance in Salesforce

Common mistakes AI coding assistants make when generating or advising on FERPA compliance in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending ShouldForget for FERPA Record Requests

**What the LLM generates:** When asked about FERPA compliance, the LLM suggests setting `Individual.ShouldForget = true` to handle a student's request to amend or delete education records, treating it identically to a GDPR right-to-erasure request.

**Why it happens:** LLM training data heavily covers GDPR, and the Individual sObject is most commonly discussed in GDPR contexts. The model conflates "data privacy request" with "erasure request" and defaults to the GDPR pattern it has seen most frequently.

**Correct pattern:**

```text
FERPA amendment requests require:
1. A separate Case record type or custom object for FERPA amendment requests
2. A workflow to review the request, approve or deny the amendment
3. If denied, allow the student/parent to place a written statement in the file
4. Retain the original record with the amendment notation — never delete

ShouldForget = true is exclusively for GDPR Article 17 erasure.
```

**Detection hint:** Look for `ShouldForget` or `right to erasure` or `delete` in any response about FERPA. FERPA does not grant a right to erasure — it grants a right to request amendment.

---

## Anti-Pattern 2: Assuming LearnerProfile FERPA Fields Auto-Enforce Access Control

**What the LLM generates:** The LLM advises setting `HasFerpaParentalDisclosure = true` and tells the user that parental access to education records is now enabled, without mentioning that additional automation, FLS, or sharing rules are needed.

**Why it happens:** The field names suggest enforcement semantics (e.g., "Has Disclosure" implies disclosure is granted). LLMs interpret boolean field names literally and assume the platform acts on them.

**Correct pattern:**

```text
HasFerpaParentalDisclosure is an informational flag only.
After setting it, you must:
1. Build a Flow or trigger that reads this flag
2. Adjust sharing rules, FLS, or Experience Cloud visibility based on the flag value
3. The flag tells your automation what to do — it does not do anything on its own
```

**Detection hint:** Look for advice that stops at "set the field to true/false" without describing the enforcement mechanism (Flow, trigger, sharing rule, FLS change).

---

## Anti-Pattern 3: Inventing Non-Existent FERPA-Specific Objects or Fields

**What the LLM generates:** The LLM references objects like `FerpaConsentRecord`, `StudentPrivacyRequest`, `FerpaDisclosureLog`, or fields like `Contact.FerpaOptOut` or `LearnerProfile.FerpaAmendmentStatus` that do not exist in standard Salesforce.

**Why it happens:** LLMs hallucinate object and field names by combining domain keywords with plausible Salesforce naming conventions. FERPA is a niche topic with limited Salesforce-specific training data, increasing hallucination risk.

**Correct pattern:**

```text
The real FERPA-relevant objects and fields in Education Cloud:
- LearnerProfile: HasFerpaParentalDisclosure, HasFerpaThrdPtyDisclosure,
  HasParentalFerpa, HasThirdPartyFerpa
- Individual: ShouldForget (GDPR only), HasOptedOutOfSolicit, SendIndividualData
- ContactPointTypeConsent: OptInStatus, EffectiveFrom, EffectiveTo, PartyId
- ContactPointConsent: ContactPointId, DataUsePurposeId

Any other FERPA-specific field or object must be custom-built.
```

**Detection hint:** Search for object or field API names that are not in the Salesforce Object Reference. Any `Ferpa` prefix on a standard object field that is not one of the four LearnerProfile fields is hallucinated.

---

## Anti-Pattern 4: Treating Directory Information Opt-Out as a Marketing Preference

**What the LLM generates:** The LLM recommends handling FERPA directory information opt-out by unsubscribing the student from email marketing using `Contact.HasOptedOutOfEmail` or Marketing Cloud suppression lists, without addressing other disclosure channels (online directories, commencement lists, third-party data feeds).

**Why it happens:** LLM training data overrepresents marketing opt-out patterns. The model maps "opt-out" to the most common Salesforce opt-out field (`HasOptedOutOfEmail`) and the most common opt-out context (marketing email).

**Correct pattern:**

```text
FERPA directory information opt-out must suppress the student from ALL
directory information disclosures, not just marketing:
- Online student directories (Experience Cloud)
- Commencement and honors lists
- Third-party integrations that export student data
- Athletic rosters and yearbook data
- Phone/email directory lookups

Use a dedicated opt-out flag (custom or Individual.HasOptedOutOfSolicit)
and check it in every channel that surfaces directory information.
```

**Detection hint:** Look for `HasOptedOutOfEmail`, `EmailOptOut`, or Marketing Cloud references in a FERPA directory opt-out context. These address only one channel.

---

## Anti-Pattern 5: Omitting the 45-Day Response Window Requirement

**What the LLM generates:** The LLM provides a comprehensive FERPA consent model design but does not mention the 45-day statutory deadline for responding to records inspection requests. The response covers data model and access control but ignores the operational compliance obligation.

**Why it happens:** LLMs tend to focus on data model and code patterns. The 45-day window is a procedural/operational requirement that does not map to a specific Salesforce object or API, so it falls outside the model's typical response patterns.

**Correct pattern:**

```text
Every FERPA implementation must include a mechanism to track the 45-day
response window for education records requests:
- Case with Entitlement Process (milestone at 45 days, warnings at 30 and 40)
- Or custom object with Date field + Scheduled Flow for deadline alerts
- Log fulfillment date and method for audit trail
- Failure to respond within 45 days is a FERPA violation
```

**Detection hint:** If the response discusses FERPA compliance without mentioning "45 days", "response window", "records request deadline", or "Entitlement Process", it is incomplete.

---

## Anti-Pattern 6: Generating Apex That Hard-Deletes Education Records

**What the LLM generates:** When asked to handle a FERPA request, the LLM generates Batch Apex that calls `Database.delete()` on student Contact or LearnerProfile records, mirroring GDPR erasure patterns.

**Why it happens:** The most common Salesforce privacy code examples in training data are GDPR erasure batches. The LLM applies the same pattern to FERPA without understanding that FERPA requires record retention.

**Correct pattern:**

```apex
// FERPA amendment — update the field, do NOT delete the record
// Log the amendment with who requested it and when
contact.FieldToAmend__c = newValue;
// Create an audit record
Ferpa_Amendment_Log__c log = new Ferpa_Amendment_Log__c(
    Contact__c = contact.Id,
    Field_Changed__c = 'FieldToAmend__c',
    Previous_Value__c = oldValue,
    New_Value__c = newValue,
    Requested_By__c = requesterId,
    Amendment_Date__c = Date.today()
);
insert log;
update contact;
```

**Detection hint:** Look for `Database.delete`, `DELETE FROM`, or anonymization patterns (replacing names with `ANON-` tokens) in a FERPA context. FERPA amendment is an update, not a delete or anonymize operation.
