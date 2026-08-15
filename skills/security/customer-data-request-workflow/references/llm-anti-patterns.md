# LLM Anti-Patterns — Customer Data Subject Request (DSR) Workflow

Mistakes AI assistants reliably make when asked to implement GDPR/CCPA data subject
rights in Salesforce.

## Anti-Pattern 1: A Bare `DELETE` With No Audit

**What the LLM generates:**

```apex
delete [SELECT Id FROM Contact WHERE Email = :subjectEmail];
```

**Why it happens:** The request is phrased as "delete the customer's data," and this
is the literal implementation.

**Correct pattern:**

```
Three things wrong, each independently disqualifying:

1. NO AUDIT. A regulator asks what you erased and when. Write an audit row
   BEFORE the DML - a failure mid-run then leaves evidence of the attempt
   rather than losing exactly the rows that failed.

2. NO SCOPE. Contact is one of a dozen objects. Build the inventory from
   Schema.DescribeSObjectResult.getChildRelationships(), then add the half
   describe cannot reach: Case Comments, Chatter, Email Messages, Notes,
   Attachments, files, long-text fields, history, and FieldHistoryArchive.

3. SOFT DELETE. A standard delete leaves restorable records in the Recycle Bin.
   Follow with Database.emptyRecycleBin or a Bulk API hard delete, and verify.

And log a HASH, never the value:
   Value_Hash__c = EncodingUtil.convertToHex(
       Crypto.generateDigest('SHA-256', Blob.valueOf(originalValue)))
An audit table holding the plaintext is a second copy of what you just erased.
```

**Detection hint:** a DSR answer containing `delete` with no audit object, no hard
delete, and a single object in scope.

---

## Anti-Pattern 2: Treating `ShouldForget` as the Erasure

**What the LLM generates:** "Set `Individual.ShouldForget = true` to mark the customer
as forgotten."

**Why it happens:** The field name states the outcome, so it reads as the action.

**Correct pattern:**

```
ShouldForget is a stored PREFERENCE:

  "Preference to delete records and personal data related to this customer."

Setting it deletes nothing. Its real value is as the ANCHOR: it records that the
request was made, starts the SLA clock, and gives downstream jobs a queryable
population. Same for SendIndividualData - "Preference to export personal data
for delivery to the customer."

Two availability constraints to state whenever recommending it:
  - "This object is available if Data Protection and Privacy is enabled."
  - "The Individual object isn't available to Customer Community, Partner
     Community, and Customer Portal users." A portal request needs a staging
     object; the community user never touches the privacy record.
```

**Detection hint:** `ShouldForget` presented as an action, or an `Individual`-based
design with no enablement check and no portal staging path.

---

## Anti-Pattern 3: Scoping to Contact and Lead

**What the LLM generates:** an erasure covering Contact, Lead, and "any related
records."

**Why it happens:** They are the objects a prompt names, and "related records" sounds
like it covers the rest.

**Correct pattern:**

```
Build the relational half from the schema:

  for (Schema.ChildRelationship cr :
           Contact.SObjectType.getDescribe().getChildRelationships()) { ... }

Then add the half describe CANNOT reach, as a fixed checklist:

  IDENTITY   portal/Experience Cloud User records; Person Accounts (which are
             Account AND Contact simultaneously)
  CONSENT    ContactPointEmail/Phone/Address, ContactPointConsent,
             ContactPointTypeConsent, AuthorizationFormConsent,
             CommunicationSubscriptionConsent, PartyConsent
  FREE TEXT  Case Comments, Chatter posts and comments, Email Messages, Notes,
             Attachments, ContentDocument/ContentVersion bodies, long-text
             description fields
  ARCHIVE    <Object>History, FieldHistoryArchive, Setup Audit Trail
  OFF-PLATFORM  backups, sandboxes, CRM Analytics datasets, warehouse extracts,
             marketing platform copies

The free-text half has no relationship to traverse and is found by searching for
the identifier value, not by walking the schema.
```

**Detection hint:** an erasure scope naming fewer than five objects, or one with no
consent objects and no content objects.

---

## Anti-Pattern 4: Forgetting `FieldHistoryArchive`

**What the LLM generates:** an erasure that deletes records and notes that "related
history is deleted automatically."

**Why it happens:** The cascade from record to `<Object>History` is real, so the model
generalises it to the archive.

**Correct pattern:**

```
The cascade stops before the archive:

  "If you delete a record in your production data, the delete cascades to the
   related history tracking records, but Salesforce doesn't delete the history
   copied into the FieldHistoryArchive big object."

In a Shield org this leaves the OLD VALUES of the very fields being erased in a
separate store. Salesforce documents a distinct procedure for deleting data in
FieldHistoryArchive; it must be an explicit runbook step.

Prove it in the sandbox rehearsal by querying FieldHistoryArchive for the
synthetic subject AFTER the workflow runs. It will return rows if the step is
missing - the easiest gap in this domain to demonstrate.

Note the exposure: field history retention policies can be set on Contacts,
Individuals, Contact Point Consent, Contact Point Type Consent, Authorization
Form Consent, Communication Subscription Consent, and Party Consent - most of
the objects an erasure targets.
```

**Detection hint:** a DSR workflow with no `FieldHistoryArchive` step in an org where
Shield or Field Audit Trail is mentioned.

---

## Anti-Pattern 5: Deleting Person Accounts

**What the LLM generates:** "Delete the Contact and the associated Account record."

**Why it happens:** A Person Account looks like a Contact in most of the prompt's
framing, and deletion is the literal request.

**Correct pattern:**

```
A Person Account is Account AND Contact simultaneously, and Orders, Cases,
Assets, and Contracts reference the Account side. Deleting it either fails on
referential integrity or cascades destructively into transactional records the
business must keep.

Default to PSEUDONYMISATION for Person Accounts: null or redact the identifying
fields, keep the record and its relationships. That satisfies erasure under most
interpretations, keeps referential integrity, and avoids the cascade.

State the choice explicitly. Deletion versus pseudonymisation is a LEGAL
position, not a technical preference, and it needs sign-off as one.
```

**Detection hint:** a hard delete of Account or Contact in a B2C context, with no
mention of Person Accounts or pseudonymisation.

---

## Anti-Pattern 6: Ignoring Sandboxes and Off-Platform Copies

**What the LLM generates:** a production-only erasure workflow, presented as complete.

**Why it happens:** The prompt is about the org, and sandboxes are a different
concern in most Salesforce documentation.

**Correct pattern:**

```
Every sandbox refreshed from production before the erasure holds a full copy
with real identifiers. So do backups, CRM Analytics datasets, warehouse
extracts, and marketing platform copies.

Two viable positions, and the runbook must state which:
  A) repeat the erasure in every environment holding a copy
  B) mask on every sandbox refresh, and cite masking as the control

(B) is far more sustainable - and it must be in place BEFORE requests start
arriving, because it does nothing for copies already taken.

Each off-platform destination needs a named owner and a stated position in the
runbook. "We deleted it in production" is not an answer to "where else is it."
```

**Detection hint:** a DSR workflow with no environment inventory and no off-platform
section.

---

## Anti-Pattern 7: Promising Complete Erasure

**What the LLM generates:** "This workflow removes all of the customer's personal
data from Salesforce."

**Why it happens:** It is the goal as stated, and qualifying it feels like failing
the request.

**Correct pattern:**

```
Some things cannot be erased, and a plan that does not say so will be found out:

  - Setup Audit Trail entries
  - certain platform-managed history
  - data retained under a COMPETING legal obligation (tax, financial services
    record-keeping, AML)

Enumerate the exceptions during DESIGN and get a written position from legal for
each: what cannot be erased, why, under which obligation, and what compensating
control applies.

Most privacy regimes accommodate a competing legal obligation. None accommodate
an unexplained residual copy. The deliverable is a residual-risk register that
lives beside the runbook.
```

**Detection hint:** any unqualified claim of complete erasure, or a workflow with no
exceptions register.

---

## Anti-Pattern 8: Treating Access and Deletion as the Same Workflow

**What the LLM generates:** one "DSR handler" that covers both a subject access
request and an erasure request.

**Why it happens:** Both are "data subject requests" and the prompt often names them
together.

**Correct pattern:**

```
They differ in scope, direction, output, and risk:

  ACCESS / PORTABILITY
    - read-only; nothing is destroyed
    - output is a package delivered to the subject, which is itself sensitive
    - Privacy Center's DsarPolicyLog tracks the generated file's lifecycle:
      when the file is deleted, and the most recent time the subject downloaded
      it - both are compliance-relevant
    - Individual.SendIndividualData is the corresponding preference

  ERASURE
    - destructive and irreversible
    - needs the object inventory, hard delete, FieldHistoryArchive, and the
      off-platform positions
    - Individual.ShouldForget is the corresponding preference

Different SLAs, different approval gates, different evidence. Model them as two
workflows sharing an Individual record, not one handler with a mode flag.
```

**Detection hint:** a single method or Flow branching on a request-type picklist, with
one shared audit and one shared approval path.
