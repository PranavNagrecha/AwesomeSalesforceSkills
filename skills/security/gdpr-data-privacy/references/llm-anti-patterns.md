# LLM Anti-Patterns — GDPR Data Privacy

Common mistakes AI coding assistants make when generating or advising on GDPR data privacy in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating ShouldForget as an Automated Erasure Trigger

**What the LLM generates:** Advice like "set `ShouldForget = true` on the Individual record to trigger the erasure process" or code that sets the flag and then considers the RTBF request fulfilled.

**Why it happens:** LLMs conflate the semantic meaning of the field name ("should forget") with platform behavior. The name implies action, but the field is passive. Training data may include Salesforce documentation that describes the field without emphasizing the absence of automated response.

**Correct pattern:**

```text
Setting ShouldForget = true is a prerequisite, not a completion.
You must also have one of:
  - Privacy Center Erasure Policy configured and active
  - A Batch Apex class (or scheduled job) that queries WHERE ShouldForget = true
    and anonymizes or deletes linked records across all in-scope objects.
The flag alone does nothing.
```

**Detection hint:** Any response that mentions `ShouldForget` without also describing an erasure automation (Privacy Center policy or Batch Apex) is incomplete. Flag responses that stop at setting the field.

---

## Anti-Pattern 2: Recommending Hard Delete of Contact Records

**What the LLM generates:** Code that uses `delete` on Contact records as the RTBF implementation, e.g., `delete [SELECT Id FROM Contact WHERE Email = :email]`.

**Why it happens:** Deletion is the most literal interpretation of "right to be forgotten." LLMs default to the straightforward interpretation without reasoning about referential integrity. This pattern is common in non-Salesforce contexts (e.g., SQL `DELETE FROM users`) and bleeds into Salesforce advice.

**Correct pattern:**

```apex
// Check for FK dependencies before any delete attempt.
// If related records exist, anonymize instead of deleting.
List<Opportunity> relatedOpps = [SELECT Id FROM Opportunity WHERE ContactId = :contactId LIMIT 1];
if (relatedOpps.isEmpty()) {
    delete contact; // safe only if no FK dependencies
} else {
    // Anonymize PII fields; preserve record shell
    contact.FirstName = 'ERASED';
    contact.LastName  = 'ERASED-' + System.now().getTime();
    contact.Email     = null;
    contact.Phone     = null;
    update contact;
}
```

**Detection hint:** Any RTBF code that uses `delete` on Contact, Lead, or PersonAccount without a prior FK check is suspect. Flag it and ask about related Opportunity, Case, Task, and Event records.

---

## Anti-Pattern 3: Scoping Erasure Only to Contact

**What the LLM generates:** An RTBF batch or service class that only anonymizes Contact records, with no mention of Lead, PersonAccount, custom objects, or related objects that may store PII (e.g., a custom `Customer_Profile__c` with fields like `SSN__c` or `DOB__c`).

**Why it happens:** Contact is the canonical "person" object in Salesforce. LLMs anchor on it because it appears most frequently in training data about personal data. The fact that PII may be distributed across many objects is non-obvious without org-specific context.

**Correct pattern:**

```text
Before building any erasure implementation, enumerate ALL objects in the org
that store personal data:
  - Contact (standard)
  - Lead (standard, including unconverted)
  - PersonAccount (if enabled)
  - Any custom objects with fields storing: name, email, phone, address,
    date of birth, national ID, or any indirect identifier
The erasure scope must cover all of them.
```

**Detection hint:** If the RTBF implementation only queries `Contact`, ask the practitioner to audit custom objects for PII fields and add them to the scope.

---

## Anti-Pattern 4: Using HasOptedOutOfEmail as the Consent System of Record

**What the LLM generates:** Code or advice that manages GDPR consent by reading and writing `Contact.HasOptedOutOfEmail`, treating it as the source of truth for marketing consent.

**Why it happens:** `HasOptedOutOfEmail` is the most familiar email consent field in Salesforce. It is prominently used in Salesforce documentation for email suppression. LLMs trained on Salesforce content associate it with "managing email consent" without understanding the GDPR distinction between suppression and documented consent.

**Correct pattern:**

```text
HasOptedOutOfEmail is an email suppression flag.
It is NOT a GDPR consent record.

For GDPR compliance:
  - Use ContactPointTypeConsent with ContactPointType='Email', OptInStatus, EffectiveFrom, CaptureDate, CaptureSource
  - Or use ContactPointConsent for per-address, per-purpose consent
  - Populate EffectiveFrom and CaptureSource at consent capture time
  - Do NOT use HasOptedOutOfEmail as the audit-ready consent record
```

**Detection hint:** If consent management advice only references `HasOptedOutOfEmail` or `Email_Opt_Out__c` without mentioning `ContactPointTypeConsent`, the advice is incomplete for GDPR use.

---

## Anti-Pattern 5: Creating One Individual Record Shared Across Multiple Contacts

**What the LLM generates:** Code that looks up an existing Individual by name or email and reuses it for a new Contact if one is found, rather than always creating a new Individual per person.

**Why it happens:** LLMs optimize for deduplication and often generate patterns that avoid creating duplicate records. Applying this logic to Individual is incorrect because the Individual is a privacy container for exactly one natural person — not a shared reference object.

**Correct pattern:**

```text
Individual records are 1:1 with natural persons.
Never share a single Individual across multiple Contact records for different people.
Each Contact (or Lead, or PersonAccount) representing a distinct natural person
must have its own Individual record.

If two Contact records represent the same natural person (e.g., a duplicate),
they may share one Individual — but this is a data quality decision, not a
default pattern. Confirm identity before sharing an Individual.
```

**Detection hint:** Any code that queries for an existing Individual using fields like `LastName` or `Email` and reuses it for a new Contact is likely wrong. Sharing Individuals by name match is a false-deduplication anti-pattern.

---

## Anti-Pattern 6: Omitting EffectiveFrom and CaptureDate on Consent Records

**What the LLM generates:** Code that inserts `ContactPointTypeConsent` or `ContactPointConsent` records without setting `EffectiveFrom`, `CaptureDate`, or `CaptureSource`. The generated record has `OptInStatus = 'OptIn'` but no timestamps.

**Why it happens:** LLMs generating minimal viable insert statements often omit optional fields. Consent timestamp fields are not required by the platform and do not cause DML errors when omitted, so LLMs do not flag them as missing.

**Correct pattern:**

```apex
ContactPointTypeConsent cptc = new ContactPointTypeConsent(
    PartyId          = individual.Id,
    ContactPointType = 'Email',
    OptInStatus      = 'OptIn',
    EffectiveFrom    = Date.today(),        // Required for GDPR audit trail
    CaptureDate      = Datetime.now(),      // When was consent captured?
    CaptureSource    = 'Web Form — GDPR Consent Banner v2' // How was it captured?
);
insert cptc;
```

**Detection hint:** Any `ContactPointTypeConsent` or `ContactPointConsent` insert that omits `EffectiveFrom` and `CaptureDate` is incomplete for GDPR purposes. These fields are the evidentiary basis for demonstrating when and how consent was obtained.
