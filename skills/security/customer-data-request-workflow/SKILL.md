---
name: customer-data-request-workflow
description: "Implement GDPR/CCPA data subject rights (access, deletion, rectification) using Salesforce Privacy Center and/or custom workflow. NOT for the underlying erasure mechanics (Individual sObject, ShouldForget, ContactPointConsent) — use security/gdpr-data-privacy. NOT for general backup or org-level data retention policy."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "gdpr deletion request from a customer"
  - "right to be forgotten in salesforce"
  - "data subject access request workflow"
  - "ccpa opt out implementation"
tags:
  - privacy
  - gdpr
  - ccpa
  - compliance
inputs:
  - "Request type (access/delete/correct)"
  - "subject identifiers"
  - "org regulatory scope"
outputs:
  - "Runbook"
  - "Privacy Center policy or Apex batch"
  - "audit log"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Customer Data Subject Request (DSR) Workflow

A data subject request is a regulatory workflow with a deadline, a scope that spans
more objects than anyone expects, and an evidentiary requirement: you must be able to
show a regulator *what* you did, *when*, and *to which records*.

**Scope of this skill.** This is the *workflow*: intake, scoping, orchestration,
evidence, rehearsal, and the operational commitments that follow. The underlying
erasure mechanics — the `Individual` sObject's full field model, `ShouldForget`
semantics in depth, `ContactPointConsent` and the consent object family — belong to
`security/gdpr-data-privacy`. They appear here only where they change a workflow
decision.

Three building blocks, and which you use changes the whole design:

| Building block | What it is |
|---|---|
| **Individual** | Stores the subject's privacy preferences. Available "if Data Protection and Privacy is enabled," and not available to Customer Community, Partner Community, or Customer Portal users. |
| **Privacy Center** | Managed policies that "anonymize or transfer personal data from your org at your customer's request," surfaced as `DsarPolicy` and `DsarPolicyLog` |
| **Custom workflow** | Policy-as-Custom-Metadata plus batch or Queueable Apex, for orgs without Privacy Center |

---

## Before Starting

1. **Separate access from erasure.** They differ in scope, direction, output, SLA,
   approval gate, and risk. Model them as two workflows sharing an `Individual`
   record, not one handler with a mode flag.

2. **Confirm Data Protection and Privacy is enabled** if the design uses
   `Individual`, and plan a staging object if requests can arrive from a portal —
   community users cannot see the object.

3. **Get the legal positions before you build**: deletion versus pseudonymisation,
   what cannot be erased and under which competing obligation, and the applicable
   deadline per jurisdiction. These are legal artifacts engineering cannot author.

4. **Name the owner of every off-platform copy**: sandboxes, backups, CRM Analytics
   datasets, warehouse extracts, marketing platform. Each needs a stated position in
   the runbook.

---

## Core Concepts

### Preferences are not actions

`Individual.ShouldForget` is the "Preference to delete records and personal data
related to this customer." `SendIndividualData` is the "Preference to export personal
data for delivery to the customer." Both are stored intentions. Their value is as the
**anchor**: they record that the request was made, start the SLA clock, and give
downstream jobs a queryable population.

### Privacy Center: policies are inactive by default

`DsarPolicy.IsActive` — "Indicates whether this policy can be used (`true`) or not
(`false`) for data subject (customer) requests. The default value is `false`." Access
requires `ReadAllData` or `PrivacyDataAccess`.

`DsarPolicyLog` is the evidence, generated as a side effect of execution so it cannot
drift from what was done. It carries the requesting subject's ID, the request and
completion timestamps, the generated file's deletion and download timestamps, an error
field, and the ID of the employee or admin who acted on the subject's behalf.

### The object inventory is the hard part

Build the relational half from `Schema.DescribeSObjectResult.getChildRelationships()`.
Then add what describe cannot reach:

```text
IDENTITY      portal/Experience Cloud Users; Person Accounts (Account AND Contact)
CONSENT       ContactPointEmail/Phone/Address, ContactPointConsent,
              ContactPointTypeConsent, AuthorizationFormConsent,
              CommunicationSubscriptionConsent, PartyConsent
FREE TEXT     Case Comments, Chatter, Email Messages, Notes, Attachments,
              ContentDocument/ContentVersion bodies, long-text fields
ARCHIVE       <Object>History, FieldHistoryArchive, Setup Audit Trail
OFF-PLATFORM  backups, sandboxes, CRM Analytics, warehouse, marketing platform
```

### The archive does not cascade

> "If you delete a record in your production data, the delete cascades to the related
> history tracking records, but Salesforce doesn't delete the history copied into the
> `FieldHistoryArchive` big object."

In a Shield org this leaves the old values of the erased fields in a separate store.
It is the most commonly missed step in this domain and the easiest to prove missing.

### Deleted is not deleted

A standard `delete` is a soft delete. Follow with `Database.emptyRecycleBin` or a Bulk
API hard delete, and verify.

### The audit must not become a second copy

Log a SHA-256 hash of the original value, never the value. Write the audit row
**before** the DML so a failure mid-run leaves evidence of the attempt.

---

## Common Patterns

### Pattern A — Privacy Center

Author object-scoped policies, **activate** them as a distinct verified step, and use
`DsarPolicyLog` as the compliance report. Completeness of the erasure equals
completeness of the object inventory. Example 2 in
[`references/examples.md`](references/examples.md).

### Pattern B — policy-as-metadata plus Queueable

`DSR_Policy__mdt` rows (object, field, action, relationship path, justification) read
via `getAll()`; a Queueable walks them, writes hashed audit rows before each DML, and
executes NULL / REDACT / DELETE per row. Compliance changes scope without an Apex
deploy. Example 4.

### Pattern C — pseudonymisation for Person Accounts

Null or redact identifying fields, keep the record and its relationships. Preserves
referential integrity across Orders, Cases, and Assets. Record the choice as a legal
position.

### Pattern D — sandbox rehearsal against a synthetic subject

Create a subject with data in every object on the inventory including the awkward ones
— a Chatter post, an email message, a file, a portal User, a consent record, a
history-tracked field. Run the workflow. Then search as an unrestricted admin for
residuals, query `FieldHistoryArchive`, and check the Recycle Bin. Record elapsed time
per object. Example 5.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| Org has Privacy Center | `DsarPolicy` + `DsarPolicyLog`; verify `IsActive` |
| No Privacy Center licence | Policy-as-Custom-Metadata + Queueable, with a hashed audit object |
| Subject is a Person Account | Pseudonymise; deleting cascades into transactional records |
| Subject has portal/Experience Cloud logins | The User record is in scope, and the portal cannot see `Individual` — stage the request |
| Org has Field Audit Trail | `FieldHistoryArchive` deletion is a mandatory separate step |
| Record retained under a competing legal obligation | Do not erase; add it to the residual-risk register with a written legal position |
| Sandboxes hold copies | Masking on refresh as the standing control; repeat erasure only for existing copies |
| Access / portability request | Read-only workflow; the generated package is itself sensitive and has its own retention |
| Volume spike after an incident | Measure per-request timings first; the deadline is per request under load |

---

## Recommended Workflow

1. **Intake and anchor.** Record the request against the subject — `Individual`
   where available, a staging object for portal-submitted requests — and start the
   SLA clock from that record.
2. **Regenerate the object inventory** from the schema for this request rather than
   reusing a list, then add the free-text, archive, and off-platform checklist items.
3. **Classify each object**: NULL, REDACT, DELETE, or retain-under-obligation. The
   retain decisions go to the residual-risk register with a legal position.
4. **Execute with evidence**: write the hashed audit row before each DML, run in
   system mode with a tightly scoped permission set and an approval gate, and make the
   run idempotent so a partial failure can be re-run.
5. **Complete the erasure**: hard delete from the Recycle Bin, delete from
   `FieldHistoryArchive`, and execute the stated position for every off-platform copy.
6. **Verify and evidence**: search as an unrestricted admin for residuals across every
   inventory item and in global search, then produce the completion record —
   `DsarPolicyLog` or the custom audit — and confirm to the requester.
7. **Rehearse quarterly in a full sandbox** against a synthetic subject, recording
   elapsed time per object so the process can be sized against post-incident volume.

---

## Review Checklist

- [ ] Access and erasure are separate workflows with separate approval gates
- [ ] Request anchored on a record that starts the SLA clock
- [ ] Object inventory regenerated from the schema, not reused
- [ ] Consent, free-text, file, and history objects present in the inventory
- [ ] `FieldHistoryArchive` deletion is an explicit step
- [ ] Hard delete follows every soft delete, and is verified
- [ ] Audit rows written **before** DML, and store a hash rather than the value
- [ ] Person Accounts pseudonymised, with the legal position recorded
- [ ] Portal-submitted requests use a staging object, not `Individual` directly
- [ ] Privacy Center policies confirmed `IsActive = true`
- [ ] Every off-platform copy has a named owner and a stated position
- [ ] Residual-risk register lists what cannot be erased and why, with legal sign-off
- [ ] Sandbox rehearsal completed against a synthetic subject, with residual search
- [ ] Per-object elapsed times measured and sized against post-incident volume

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **`ShouldForget` is a preference, not an action.**
2. **The `Individual` object is off by default and invisible to portal users.**
3. **A Privacy Center policy defaults to inactive.**
4. **Deleting the record does not delete the archived field history.**
5. **Deleted is not deleted until it leaves the Recycle Bin.**
6. **Person Accounts are two objects wearing one record.**
7. **Free-text fields have no relationship to traverse.**
8. **Sandboxes hold a full copy of everything you just erased.**
9. **The audit trail can become a second copy of the data.**
10. **Some records cannot be deleted**, and that needs a written legal position.
11. **The deadline is measured per request, under load.**

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Object inventory | Regenerated per request: relational half from describe, plus the free-text, consent, archive, and off-platform checklist, each classified NULL / REDACT / DELETE / retain |
| Erasure runbook | Ordered steps including hard delete, `FieldHistoryArchive`, and the stated position for every off-platform copy, with an owner per step |
| Evidence record | `DsarPolicyLog` or a hashed custom audit: object, record Id, field, action, timestamp, hash — and never the value |
| Residual-risk register | What cannot be erased, under which competing obligation, with the compensating control and legal sign-off |
| Rehearsal report | Synthetic-subject run in a full sandbox: residuals found, archive query result, Recycle Bin check, and elapsed time per object |
| Completion confirmation | What was sent to the requester and when, retained per the org's own retention policy |

---

## Related Skills

- `security/gdpr-data-privacy` — the erasure mechanics this workflow orchestrates:
  the `Individual` object in depth, `ShouldForget` semantics, and the consent object
  family
- `security/field-audit-trail` — the `FieldHistoryArchive` store and its separate
  deletion procedure
- `security/sandbox-data-masking` — the standing control that makes sandbox copies a
  documented position rather than a residual exposure
- `security/data-classification-labels` — the classification that tells you which
  fields are in scope before a request arrives
