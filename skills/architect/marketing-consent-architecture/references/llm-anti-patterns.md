# LLM Anti-Patterns — Marketing Consent Architecture

Common mistakes AI coding assistants make when generating or advising on Marketing Consent Architecture. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating HasOptedOutOfEmail on Contact as the Consent System of Record

**What the LLM generates:** Advice to set `Contact.HasOptedOutOfEmail = true` to suppress marketing emails, and to check this field in all send logic as the consent gate.

**Why it happens:** `HasOptedOutOfEmail` is a widely documented legacy field that appears in almost all Salesforce CRM training data. LLMs pattern-match to it because it is syntactically simple and frequently referenced in basic "how to opt out a contact" tutorials. The platform consent objects (Individual, ContactPointTypeConsent) are newer and less represented in training data.

**Correct pattern:**
```
1. Ensure the Contact has an Individual record (Individual.Id ≠ null).
2. Create or update a ContactPointTypeConsent record:
   - IndividualId = Contact.IndividualId
   - ContactPointType = 'Email'
   - PrivacyConsentStatus = 'OptOut'
   - DataUsePurpose = [Id of the relevant Data Use Purpose record]
   - CaptureDate = now
   - CaptureSource = 'Preference Center'
3. Optionally also update Individual.HasOptedOutOfEmail = true for legacy channels.
```

**Detection hint:** Look for advice that stops at `Contact.HasOptedOutOfEmail` or `Individual.HasOptedOutOfEmail` without mentioning `ContactPointTypeConsent` or `DataUsePurpose`. That advice is incomplete for any GDPR or CCPA regulated use case.

---

## Anti-Pattern 2: Assuming MC and CRM Consent Are Automatically Synchronized

**What the LLM generates:** Instructions that say "when a subscriber unsubscribes in Marketing Cloud, the CRM Contact's opt-out field is automatically updated" or "the Marketing Cloud Connect integration keeps consent in sync."

**Why it happens:** LLMs conflate the general data sync that Marketing Cloud Connect provides (syncing Contact fields to MC Data Extensions) with the specific Consent Management integration that causes MC to read CRM consent objects at send time and write back unsubscribes. The distinction is not obvious from general descriptions of Marketing Cloud Connect.

**Correct pattern:**
```
Marketing Cloud Connect data sync ≠ Consent Management integration.

- Data sync: Contact/Lead fields replicated to MC Data Extensions on schedule.
- Consent Management: MC queries CRM ContactPointTypeConsent at send time.
  Requires explicit configuration in MC connector settings + Data Use Purpose mapping.

MC unsubscribe writeback to CRM:
  - Requires Consent Management integration to be enabled.
  - Requires the writeback option to be configured.
  - Should be validated with an end-to-end test.
```

**Detection hint:** Look for phrases like "automatically syncs" or "Marketing Cloud Connect handles consent" without a specific reference to Consent Management integration configuration steps. Flag as requiring verification.

---

## Anti-Pattern 3: Creating ContactPointTypeConsent Without DataUsePurpose

**What the LLM generates:** Apex or Flow code that creates ContactPointTypeConsent records with `ContactPointType` and `PrivacyConsentStatus` but no `DataUsePurpose` lookup.

**Why it happens:** The DataUsePurpose relationship is optional at the database level — the platform does not throw an error if it is omitted. LLMs generate the minimum code needed to satisfy the visible field requirements and do not know that missing DataUsePurpose breaks the MC Consent Management integration's send-time suppression logic.

**Correct pattern:**
```apex
// Always resolve or create DataUsePurpose before inserting ContactPointTypeConsent
Id purposeId = [
    SELECT Id FROM DataUsePurpose
    WHERE Name = 'Email Marketing' LIMIT 1
].Id;

ContactPointTypeConsent cptc = new ContactPointTypeConsent(
    IndividualId = contact.IndividualId,
    ContactPointType = 'Email',
    PrivacyConsentStatus = 'OptOut',
    DataUsePurposeId = purposeId,      // REQUIRED — do not omit
    CaptureDate = System.now(),
    CaptureContactPointType = 'Email',
    CaptureSource = 'Preference Center'
);
insert cptc;
```

**Detection hint:** Look for `ContactPointTypeConsent` insert or upsert code that does not include `DataUsePurposeId`. Flag as incomplete.

---

## Anti-Pattern 4: Pointing ContactPointTypeConsent to Contact.Id Instead of Contact.IndividualId

**What the LLM generates:** Code like `cptc.IndividualId = contact.Id;` — using the Contact's record Id as the IndividualId value.

**Why it happens:** LLMs conflate the Contact record with the Individual record. Because the field is called `IndividualId` and a Contact represents an individual person, LLMs assume the Contact Id is correct. In practice, `ContactPointTypeConsent.IndividualId` is a lookup to the `Individual` object, which is a separate record linked to the Contact via `Contact.IndividualId`. The two Ids are different.

**Correct pattern:**
```apex
// If Contact.IndividualId is null, create an Individual first
if (contact.IndividualId == null) {
    Individual ind = new Individual(
        LastName = contact.LastName,
        FirstName = contact.FirstName
    );
    insert ind;
    contact.IndividualId = ind.Id;
    update contact;
}

ContactPointTypeConsent cptc = new ContactPointTypeConsent(
    IndividualId = contact.IndividualId,  // NOT contact.Id
    ContactPointType = 'Email',
    PrivacyConsentStatus = 'OptOut'
);
```

**Detection hint:** Look for `IndividualId = [Contact Id variable]` in ContactPointTypeConsent insert code. The Contact's Id and the Individual's Id are different records — using Contact.Id here silently creates a broken consent record.

---

## Anti-Pattern 5: Recommending a Single Global Opt-Out Instead of Per-Purpose Architecture for GDPR Orgs

**What the LLM generates:** Advice to create a single "Email Opt Out" consent record per person and use it to gate all email sends, marketing and transactional alike.

**Why it happens:** A single opt-out is simpler to implement and explain. LLMs optimize for simplicity and do not automatically reason about the legal distinction between different lawful bases. The GDPR requirement that consent withdrawal for one purpose does not affect processing under a different lawful basis (e.g., contract performance) requires multiple consent records, which LLMs do not generate unless explicitly prompted.

**Correct pattern:**
```
For GDPR-regulated orgs:

Data Use Purpose: "Email Marketing" — LegalBasis: Consent
  ContactPointTypeConsent — PrivacyConsentStatus: OptOut (when subscriber opts out)

Data Use Purpose: "Email Transactional" — LegalBasis: ContractPerformance
  ContactPointTypeConsent — PrivacyConsentStatus: OptIn (unaffected by marketing opt-out)

MC journeys must be mapped to the correct Data Use Purpose.
A marketing unsubscribe suppresses Marketing sends only.
Transactional sends (account statements, security alerts) continue lawfully.
```

**Detection hint:** Look for consent architecture advice that models email as a single opt-in/opt-out with no DataUsePurpose distinction. For GDPR orgs, ask "does this handle the case where a customer withdraws marketing consent but needs to keep receiving account statements?" — if the answer requires no design change, the architecture is too coarse.
