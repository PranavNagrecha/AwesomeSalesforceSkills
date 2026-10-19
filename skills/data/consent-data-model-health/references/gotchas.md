# Gotchas — Consent Data Model Health

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Consent Records Don't Change Who Can See Clinical Records

**What happens:** A team assumes a signed AuthorizationFormConsent opens a patient's clinical records to the care team, or that withdrawing consent hides them. Neither happens.

**When it occurs:** AuthorizationFormConsent is documented as the date and way in which someone consented to a form. Its associated objects are its own share object and owner sharing rules; none of its fields relate to the sharing of other records.

**How to avoid:** Design PHI access (OWDs, sharing rules, permission sets) as its own workstream, test it with the sharing tools on specific records, and document it separately from the consent design.

---

## Gotcha 2: `ConsentGiverId` Accepts Five Object Types

**What happens:** Intake writes a Contact Id into `ConsentGiverId`. The record saves. The enrollment gate, written for Individual Ids, finds nothing and blocks the patient.

**When it occurs:** The Object Reference lists `ConsentGiverId` as a polymorphic lookup to Account, Contact, Individual, Lead, and User. Implementations that started from Contact, or flows that pass the triggering record's Id, write whatever Id is at hand.

**How to avoid:** Pick one giver type (this skill assumes Individual) and resolve it before insert: `SELECT IndividualId FROM Contact WHERE Id = :contactId`. In Apex, check `consentGiverId.getSObjectType() == Individual.SObjectType` before insert. Audit with `ConsentGiver.Type` in SOQL, as the Apex guide does with `What.Type` for polymorphic fields.

---

## Gotcha 3: The Enrollment Gate Isn't in the Data Model

**What happens:** CareProgramEnrollee records are activated for patients with no signed consent.

**When it occurs:** None of the consent objects reference CareProgramEnrollee, and nothing in their definitions blocks another record's status change. Any "no enrollment without consent" rule has to be built.

**How to avoid:** Add a before-save record-triggered flow or Apex trigger on CareProgramEnrollee that runs the purpose-specific check from SKILL.md Pattern 2 and blocks the change with an error when it returns false. Ship it with the rest of the consent metadata so sandboxes and new orgs get it too.

---

## Gotcha 4: Editing Form Text in Place Rewrites What Patients Appear to Have Signed

**What happens:** Legal updates the wording; someone replaces the document on the existing AuthorizationFormText. Every earlier consent now points at the new wording.

**When it occurs:** AuthorizationFormConsent stores `AuthorizationFormTextId`, "the authorization form text that the Individual consented to," and `ContentDocumentId` and `DetailAuthorizationFormText` on the text record are updateable.

**How to avoid:** Treat form texts as versions. Create a new AuthorizationFormText for each wording, point the form's `DefaultAuthFormTextId` at it, and leave old texts untouched. Restrict edit on AuthorizationFormText to the people who own the legal text.

---

## Gotcha 5: `Status` Is a Restricted Picklist With Three Values

**What happens:** Code and reports only know `Seen` and `Signed`, so rejections are stored by deleting rows or by reusing `Seen`; or a migration sends `Approved` and rows fail.

**When it occurs:** The Object Reference lists `Status` values Rejected, Seen, and Signed, and marks the field a restricted picklist; for restricted picklists, "Users can't load unapproved values through the API." Whether a different-case value such as `signed` is accepted is something to test in a sandbox, not assume.

**How to avoid:** Map legacy statuses to the three values before loading, use constants in Apex and picklist choices in flows, record declines as `Rejected`, and audit with `SELECT Status, COUNT(Id) FROM AuthorizationFormConsent GROUP BY Status`.

---

## Gotcha 6: Purposes Attach to the Form, Not the Form Text

**What happens:** A consent check filters on a relationship path from the form text to the purposes, which doesn't exist, or a setup links purposes to each text version and the links drift.

**When it occurs:** AuthorizationFormDataUse has `AuthorizationFormId` and `DataUsePurposeId`. The chain from a consent to a purpose is consent → form text → form → data use → purpose.

**How to avoid:** Link purposes once per form. To check consent for a purpose, collect the form Ids for the purpose from AuthorizationFormDataUse, then look for a signed consent whose `AuthorizationFormText.AuthorizationFormId` is in that set.

---

## Gotcha 7: Source and Source Type Are Different Fields

**What happens:** Intake writes `Web` into `ConsentCapturedSource` and leaves `ConsentCapturedSourceType` empty, or tries to write a URL into the type field and fails.

**When it occurs:** `ConsentCapturedSource` is a string ("For example, user@example.com, www.example.com"). `ConsentCapturedSourceType` is a restricted picklist: Email, InPerson, MailingAddress, Phone, Social, Video, Web. Both are described as required, as is `ConsentCapturedDateTime`.

**How to avoid:** Fill both: the type from the channel (`Web`), the source with the specific address or URL, and the capture time from the system clock.
