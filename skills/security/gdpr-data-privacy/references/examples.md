# Examples — GDPR Data Privacy

## Example 1: Linking Contacts to the Individual Object and Capturing Channel Consent

**Context:** A B2C Salesforce org stores European customers as Contacts. The legal team requires GDPR-compliant consent records before sending marketing emails. The org has no existing Individual or consent records.

**Problem:** Without Individual linkage, there is no GDPR-compliant consent container. Consent stored only as `HasOptedOutOfEmail` on Contact provides no capture date, no consent window, no channel granularity, and no audit history. If a regulator requests proof of consent, Contact fields alone cannot satisfy Article 7 requirements.

**Solution:**

```apex
// Trigger on Contact insert/update to create Individual and consent record.
// In production, move logic to a handler class; shown inline for clarity.

trigger ContactPrivacySetup on Contact (after insert) {
    List<Individual> individualsToInsert = new List<Individual>();
    Map<Id, Contact> contactsNeedingIndividual = new Map<Id, Contact>();

    for (Contact c : Trigger.new) {
        if (c.IndividualId == null) {
            Individual ind = new Individual(
                LastName       = c.LastName,
                ShouldForget   = false,
                HasOptedOutOfSolicit = false
            );
            individualsToInsert.add(ind);
            contactsNeedingIndividual.put(c.Id, c);
        }
    }

    if (individualsToInsert.isEmpty()) return;

    insert individualsToInsert;

    // Link Individual back to Contact
    List<Contact> contactsToUpdate = new List<Contact>();
    Integer i = 0;
    for (Id contactId : contactsNeedingIndividual.keySet()) {
        contactsToUpdate.add(new Contact(
            Id           = contactId,
            IndividualId = individualsToInsert[i].Id
        ));
        i++;
    }
    update contactsToUpdate;

    // Create email channel consent record (default: Unknown until confirmed)
    List<ContactPointTypeConsent> consents = new List<ContactPointTypeConsent>();
    for (Individual ind : individualsToInsert) {
        consents.add(new ContactPointTypeConsent(
            PartyId          = ind.Id,
            ContactPointType = 'Email',
            OptInStatus      = 'Unknown',
            EffectiveFrom    = System.today()
        ));
    }
    insert consents;
}
```

**Why it works:** Each Contact now has a dedicated Individual record as its privacy container. The `ContactPointTypeConsent` record for the Email channel starts with `OptInStatus = Unknown`, forcing an explicit opt-in step before marketing sends. `EffectiveFrom` captures the date the record was created, providing an audit timestamp. When the data subject opts in (e.g., via a web form), update `OptInStatus` to `OptIn` and set `CaptureDate` and `CaptureSource` on the consent record.

---

## Example 2: Handling a Right to Erasure Request Without Privacy Center

**Context:** A data subject submits a GDPR erasure request. The org does not have Privacy Center licensed. The Contact has associated Opportunities and Cases, so hard delete will fail or produce orphaned records.

**Problem:** The team initially attempts `delete [SELECT Id FROM Contact WHERE Email = :requestEmail]`. This throws a `DmlException` because related Opportunity and Case records have lookups to Contact. Even if the delete succeeded, it would leave Opportunities with a null Contact, breaking sales reporting.

**Solution:**

```apex
// DataSubjectErasureService.cls
// Called from a DSR intake flow or manual process once identity is verified.

public class DataSubjectErasureService {

    public static void anonymizeByEmail(String requestorEmail) {
        // 1. Find matching Contacts
        List<Contact> contacts = [
            SELECT Id, IndividualId, FirstName, LastName, Email, Phone,
                   MailingStreet, MailingCity, MailingPostalCode, MailingCountry,
                   Birthdate, Description
            FROM Contact
            WHERE Email = :requestorEmail
        ];

        if (contacts.isEmpty()) return;

        Set<Id> individualIds = new Set<Id>();
        String anonToken = 'ERASED-' + String.valueOf(System.now().getTime());

        for (Contact c : contacts) {
            if (c.IndividualId != null) individualIds.add(c.IndividualId);
            c.FirstName        = 'ERASED';
            c.LastName         = anonToken;
            c.Email            = null;
            c.Phone            = null;
            c.MailingStreet    = null;
            c.MailingCity      = null;
            c.MailingPostalCode = null;
            c.MailingCountry   = null;
            c.Birthdate        = null;
            c.Description      = null;
        }
        update contacts;

        // 2. Mark Individual as forgotten
        if (!individualIds.isEmpty()) {
            List<Individual> individuals = [
                SELECT Id, ShouldForget FROM Individual WHERE Id IN :individualIds
            ];
            for (Individual ind : individuals) {
                ind.ShouldForget = true;
            }
            update individuals;
        }

        // 3. Anonymize linked Leads (if email matches and not converted)
        List<Lead> leads = [
            SELECT Id, FirstName, LastName, Email, Phone, Street
            FROM Lead
            WHERE Email = :requestorEmail AND IsConverted = false
        ];
        for (Lead l : leads) {
            l.FirstName = 'ERASED';
            l.LastName  = anonToken;
            l.Email     = null;
            l.Phone     = null;
            l.Street    = null;
        }
        if (!leads.isEmpty()) update leads;

        // 4. Write audit record (custom object: DSR_Audit__c)
        DSR_Audit__c audit = new DSR_Audit__c(
            Request_Type__c   = 'Right to Erasure',
            Fulfilled_Date__c = System.today(),
            Records_Affected__c = contacts.size() + leads.size(),
            Anonymization_Token__c = anonToken
        );
        insert audit;
    }
}
```

**Why it works:** Anonymization replaces all personal data fields with a non-identifying token while preserving the Contact record shell. Opportunities and Cases retain their Contact lookup without FK errors. The `DSR_Audit__c` record provides the audit trail required to demonstrate compliance if the fulfillment is challenged. The same token value appears across all anonymized records, making it possible to verify the scope of a specific erasure event.

---

## Example 3: Per-Purpose Consent with ContactPointConsent and DataUsePurpose

**Context:** An org processes personal data for two distinct purposes: transactional email (lawful basis: contract performance) and marketing email (lawful basis: consent). The org must track consent for marketing independently of transactional communication rights.

**Problem:** Using only `ContactPointTypeConsent` with `ContactPointType = Email` cannot distinguish between transactional and marketing purposes. If the data subject withdraws marketing consent, the org must still send transactional emails — but a single channel-level opt-out would suppress both.

**Solution:**

```apex
// Create a DataUsePurpose record for marketing (done once via setup or data load)
DataUsePurpose marketingPurpose = new DataUsePurpose(
    Name        = 'Email Marketing',
    Description = 'Sending promotional and product update emails. Lawful basis: Consent (GDPR Art. 6(1)(a)).',
    LegalBasis  = 'Consent',
    IsActive    = true
);
insert marketingPurpose;

// For each Contact's email address, create a ContactPointConsent
// ContactPointEmail is the platform object linking an email address to a Contact
ContactPointEmail cpe = [
    SELECT Id FROM ContactPointEmail WHERE ParentId = :contactId LIMIT 1
];

ContactPointConsent cpc = new ContactPointConsent(
    Name              = 'Marketing Email Consent — ' + contactId,
    ContactPointId    = cpe.Id,
    DataUsePurposeId  = marketingPurpose.Id,
    OptInStatus       = 'OptIn',
    EffectiveFrom     = Date.today(),
    CaptureDate       = Datetime.now(),
    CaptureSource     = 'Web Form — Spring Campaign 2025',
    PartyId           = individual.Id
);
insert cpc;
```

**Why it works:** `ContactPointConsent` binds consent to a specific contact point (the email address record) and a specific processing purpose (marketing), not just a channel. When the data subject withdraws marketing consent, set `OptInStatus = OptOut` and `EffectiveTo = Date.today()` on this record only. Transactional consent, stored under a separate `ContactPointConsent` with a different `DataUsePurposeId`, is unaffected. This models the GDPR principle of purpose limitation at the data level.

---

## Anti-Pattern: Treating HasOptedOutOfEmail as GDPR Consent

**What practitioners do:** Use the standard `Contact.HasOptedOutOfEmail` checkbox as the sole mechanism for GDPR consent management. When a customer opts in, uncheck it; when they opt out, check it.

**What goes wrong:** `HasOptedOutOfEmail` is a binary current-state flag with no timestamps, no consent capture source, no per-purpose granularity, and no history. Under GDPR Article 7, you must be able to demonstrate that consent was freely given, specific, informed, and unambiguous — and prove when and how it was obtained. A checkbox with no audit trail cannot do this. Furthermore, flipping the checkbox does not create an audit history; prior consent states are permanently lost.

**Correct approach:** Use `ContactPointTypeConsent` (for channel-level consent) and `ContactPointConsent` (for purpose-level consent) linked via `PartyId` to an Individual record. Populate `EffectiveFrom`, `CaptureDate`, and `CaptureSource` at consent capture time. Keep the old consent record and create a new one when consent changes, preserving the full history. Optionally use `HasOptedOutOfEmail` as a derived flag for send-time suppression, but do not treat it as the system of record for GDPR consent.
