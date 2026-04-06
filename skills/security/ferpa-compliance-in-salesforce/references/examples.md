# Examples — FERPA Compliance in Salesforce

## Example 1: Configuring LearnerProfile FERPA Fields with Consent Automation

**Context:** A university running Education Cloud needs to track parental and third-party disclosure consent for each student. Admissions staff update consent forms manually, but there is no audit trail and no connection between the paper consent and the LearnerProfile record.

**Problem:** Without automation, FERPA boolean fields on LearnerProfile are updated inconsistently. Some students show `HasFerpaParentalDisclosure = true` with no supporting consent record. During a Department of Education review, the institution cannot prove when consent was granted.

**Solution:**

```apex
// Flow-triggered Apex: when a ContactPointTypeConsent record is created or updated
// with a DataUsePurpose named "FERPA Parental Disclosure", update the linked
// LearnerProfile's HasFerpaParentalDisclosure field.

public class FerpaConsentHandler {

    public static void syncConsentToLearnerProfile(List<ContactPointTypeConsent> consents) {
        Set<Id> individualIds = new Set<Id>();
        Map<Id, Boolean> parentalConsentMap = new Map<Id, Boolean>();
        Map<Id, Boolean> thirdPartyConsentMap = new Map<Id, Boolean>();

        for (ContactPointTypeConsent cptc : consents) {
            individualIds.add(cptc.PartyId);
        }

        // Query DataUsePurpose to distinguish parental vs third-party
        for (ContactPointTypeConsent cptc : [
            SELECT Id, PartyId, OptInStatus, DataUsePurpose.Name
            FROM ContactPointTypeConsent
            WHERE PartyId IN :individualIds
              AND DataUsePurpose.Name IN ('FERPA Parental Disclosure', 'FERPA Third Party Disclosure')
        ]) {
            Boolean isOptedIn = (cptc.OptInStatus == 'OptIn');
            if (cptc.DataUsePurpose.Name == 'FERPA Parental Disclosure') {
                parentalConsentMap.put(cptc.PartyId, isOptedIn);
            } else {
                thirdPartyConsentMap.put(cptc.PartyId, isOptedIn);
            }
        }

        // Find LearnerProfiles linked through Contact -> Individual
        List<Contact> contacts = [
            SELECT Id, IndividualId
            FROM Contact
            WHERE IndividualId IN :individualIds
        ];

        Map<Id, Id> individualToContact = new Map<Id, Id>();
        for (Contact c : contacts) {
            individualToContact.put(c.IndividualId, c.Id);
        }

        List<LearnerProfile> profiles = [
            SELECT Id, ContactId, HasFerpaParentalDisclosure, HasFerpaThrdPtyDisclosure
            FROM LearnerProfile
            WHERE ContactId IN :individualToContact.values()
        ];

        for (LearnerProfile lp : profiles) {
            Id contactId = lp.ContactId;
            for (Id indId : individualToContact.keySet()) {
                if (individualToContact.get(indId) == contactId) {
                    if (parentalConsentMap.containsKey(indId)) {
                        lp.HasFerpaParentalDisclosure = parentalConsentMap.get(indId);
                    }
                    if (thirdPartyConsentMap.containsKey(indId)) {
                        lp.HasFerpaThrdPtyDisclosure = thirdPartyConsentMap.get(indId);
                    }
                }
            }
        }

        update profiles;
    }
}
```

**Why it works:** The consent record (ContactPointTypeConsent) becomes the source of truth. The LearnerProfile FERPA booleans are derived from consent records, creating a traceable link between the consent event and the flag state. Auditors can query consent records with `EffectiveFrom` timestamps to verify when disclosure was authorized.

---

## Example 2: 45-Day FERPA Records Request Tracking with Entitlement Process

**Context:** A K-12 district receives 30+ FERPA records requests per semester from parents requesting to inspect their child's education records. The registrar tracks these in a spreadsheet. Two requests exceeded the 45-day window last year, triggering a complaint to the Family Policy Compliance Office.

**Problem:** Without SLA-enforced tracking in Salesforce, the 45-day deadline is easily missed during busy enrollment periods.

**Solution:**

```text
Configuration steps (declarative):

1. Create a Case Record Type: "FERPA Records Request"
   - Fields: Student Contact (lookup), Request Date, Request Type (picklist: Inspect,
     Amend, Explanation of Rights), Fulfillment Date, Fulfillment Method (picklist:
     In-Person Review, Mailed Copy, Electronic Copy)

2. Create an Entitlement Process: "FERPA 45-Day Response"
   - Entry Criteria: Case.RecordType.Name = 'FERPA Records Request'
   - Milestone: "Response Due"
     - Time Trigger: 45 calendar days from Case.CreatedDate
     - Success Criteria: Case.Status = 'Fulfilled' OR Case.Status = 'Closed'
   - Milestone: "30-Day Warning"
     - Time Trigger: 30 calendar days from Case.CreatedDate
     - Violation Action: Email alert to registrar and compliance officer
   - Milestone: "40-Day Escalation"
     - Time Trigger: 40 calendar days from Case.CreatedDate
     - Violation Action: Email alert to registrar supervisor + Task assigned to compliance officer

3. Create a Flow: "Auto-Set Entitlement on FERPA Case"
   - Trigger: Case created with RecordType = 'FERPA Records Request'
   - Action: Set EntitlementId to the "FERPA 45-Day Response" Entitlement record
```

**Why it works:** The Entitlement Process provides built-in SLA tracking with milestone timers, warning actions, and escalation. Compliance officers get automatic alerts at 30 and 40 days, preventing deadline misses. The Case record provides an audit trail of request intake, fulfillment, and response method.

---

## Anti-Pattern: Using ShouldForget for FERPA Records Amendment

**What practitioners do:** When a student requests amendment of an education record under FERPA, the admin sets `Individual.ShouldForget = true` on the student's Individual record, assuming this will trigger the correction process.

**What goes wrong:** `ShouldForget` is a GDPR right-to-erasure flag. If the org has GDPR automation (Privacy Center policies or Batch Apex), setting this flag triggers deletion or anonymization of the student's personal data — destroying education records that FERPA requires the institution to retain. FERPA amendment is a correction or annotation, not an erasure. The institution must either amend the record as requested or provide a formal hearing process. Records must be retained with the amendment notation.

**Correct approach:** Create a separate FERPA amendment workflow using a Case record type or custom object. The workflow should: (1) record the requested change, (2) route to the appropriate decision-maker, (3) if approved, update the specific field and log the amendment with a timestamp, (4) if denied, attach a written explanation and allow the student/parent to place a statement in the file. Never set `ShouldForget = true` for a FERPA amendment request.
