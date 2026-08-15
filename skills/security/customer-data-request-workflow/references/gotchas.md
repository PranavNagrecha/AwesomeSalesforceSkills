# Gotchas — Customer Data Subject Request (DSR) Workflow

Non-obvious platform behaviours that leave residual personal data after an erasure
that looked complete.

## Gotcha 1: `ShouldForget` Is a Preference, Not an Action

**What happens:** A team sets `Individual.ShouldForget = true` and considers the
request honoured. Nothing has been deleted.

The Object Reference is precise: `ShouldForget` is the "Preference to delete records
and personal data related to this customer." Likewise `SendIndividualData` is the
"Preference to export personal data for delivery to the customer." Both are stored
intentions.

**When it occurs:** On the first request in an org that has enabled Data Protection
and Privacy but has not built the process behind it.

**How to avoid:** Treat the flag as the *anchor*, which is its real value: it records
that the request was made, starts the SLA clock, and gives every downstream job a
queryable population. Then build the job that acts on it. A design that treats the
checkbox as the erasure has a compliance record with no compliance action behind it.

---

## Gotcha 2: The Individual Object Is Off by Default and Invisible to Portal Users

**What happens:** A design assumes `Individual` exists, and it does not. Or a
self-service privacy page is built on Experience Cloud and the object cannot be
queried there.

> "This object is available if Data Protection and Privacy is enabled."
>
> "The Individual object isn't available to Customer Community, Partner Community,
> and Customer Portal users."
> — Object Reference, *Individual* / *IndividualHistory*

**When it occurs:** At the start of the build, and again when someone proposes a
customer-facing preference centre.

**How to avoid:** Confirm the setting is enabled before designing around the object.
For a portal-submitted request, stage it on a custom object the community user *can*
write to, and have an internal process create or update the `Individual` record. The
portal never touches the privacy record directly.

---

## Gotcha 3: A Privacy Center Policy Defaults to Inactive

**What happens:** DSAR policies are authored, deployed, and reviewed. Requests
produce no effect, and there is no error — because an inactive policy is simply not
available to run.

> "`IsActive` — Indicates whether this policy can be used (`true`) or not (`false`)
> for data subject (customer) requests. **The default value is `false`.**"
> — Object Reference, *DsarPolicy*

**When it occurs:** Between deployment and the first real request, which can be weeks
apart.

**How to avoid:** Make activation a distinct, separately verified step in the
deployment, and query `DsarPolicy` for `IsActive = false` as a standing check. Note
the access requirement while you are there: the object "is for Privacy Center
customers with the `ReadAllData` or `PrivacyDataAccess` permissions," so the person
running the check needs one of those.

---

## Gotcha 4: Deleting the Record Does Not Delete the Archived Field History

**What happens:** An erasure completes, the records are gone, and the subject's old
field values remain in the Shield archive — including the values of the very fields
that were redacted.

> "If you delete a record in your production data, the delete cascades to the related
> history tracking records, but Salesforce doesn't delete the history copied into the
> `FieldHistoryArchive` big object."
> — Salesforce Security Guide, *Field Audit Trail*

**When it occurs:** In any org with Field Audit Trail — that is, any org that bought
Shield for compliance reasons, which is the same population most likely to receive
DSRs.

**How to avoid:** Add `FieldHistoryArchive` as an explicit step in the erasure
runbook, using Salesforce's documented procedure for deleting data there. Verify it in
the sandbox rehearsal by querying the archive for the synthetic subject after the
workflow runs — it *will* return rows if the step is missing, which makes this the
easiest gap to prove.

Note how wide the exposure is: field history retention policies can be set on
Contacts, Individuals, Contact Point Consent, Contact Point Type Consent,
Authorization Form Consent, Communication Subscription Consent, and Party Consent
among others — most of the objects a privacy erasure targets.

---

## Gotcha 5: Deleted Is Not Deleted Until It Leaves the Recycle Bin

**What happens:** A `delete` succeeds, the records disappear from list views, and the
erasure is signed off. The records are in the Recycle Bin, restorable, and still
contain the subject's data.

**When it occurs:** Every time, unless the runbook says otherwise — a standard
`delete` is a soft delete.

**How to avoid:** Follow every DSR deletion with an explicit hard delete
(`Database.emptyRecycleBin`, or the Bulk API hard delete operation), and verify the
Recycle Bin is empty of the subject's records as a separate check. Add it to the
sandbox rehearsal's residual-data queries so a missing hard delete fails the
rehearsal rather than the audit.

---

## Gotcha 6: Person Accounts Are Two Objects Wearing One Record

**What happens:** An erasure scoped to Contact misses half of a Person Account's data,
or a deletion attempt fails on referential integrity because Orders, Cases, or Assets
reference the Account side.

**When it occurs:** In every B2C org, and in any org where Person Accounts were
enabled for one business unit years ago and nobody remembers.

**How to avoid:** Scope Person Accounts explicitly in the object inventory, and
default to **pseudonymisation over deletion** for them: null or redact the identifying
fields while leaving the record and its relationships intact. That satisfies erasure
requirements in most interpretations, keeps referential integrity, and avoids a
cascade of failed deletes across transactional objects. Whichever you choose, record
which one and why — the choice is a legal position, not a technical preference, and it
should be signed off as one.

---

## Gotcha 7: Free-Text Fields Have No Relationship to Traverse

**What happens:** A describe-driven inventory finds every object with a lookup to
Contact and misses the subject's name and email sitting in a case comment, a Chatter
post, an email message body, and a file.

**When it occurs:** Always, because relationship traversal cannot reach content.

**How to avoid:** Split the inventory into two halves. The relational half comes from
`getChildRelationships()`. The content half is a fixed checklist — Case Comments,
Chatter posts and comments, Email Messages, Notes, Attachments,
`ContentDocument`/`ContentVersion` file bodies, and long-text description fields on
every in-scope object — searched by identifier value rather than by relationship. The
sandbox rehearsal's residual search (global search for the synthetic subject's name,
email, and phone) is what proves the second half is complete.

---

## Gotcha 8: Sandboxes Hold a Full Copy of Everything You Just Erased

**What happens:** Production erasure completes. Four sandboxes refreshed from
production last month still contain the subject's data, in full, with real
identifiers.

**When it occurs:** In every org with sandboxes, which is every org.

**How to avoid:** Decide the position and write it down. Either the erasure is
repeated in every sandbox that holds a copy, or data masking runs on every refresh and
that masking is the documented control. The second is far more sustainable, and it has
to be in place *before* the requests start arriving — retrofitting masking does not
help with copies already taken. See `security/sandbox-data-masking`.

The same reasoning extends to backups, CRM Analytics datasets, data warehouse
extracts, and marketing platform copies. Each needs a named owner and a stated
position in the DSR runbook.

---

## Gotcha 9: The Audit Trail Can Become a Second Copy of the Data

**What happens:** A well-intentioned audit object records, per erased field, the old
value — so the team can prove what was removed. The audit table is now a complete,
queryable copy of the personal data the erasure was supposed to destroy.

**When it occurs:** In custom-built DSR workflows, where "log what we changed" is the
obvious way to produce evidence.

**How to avoid:** Log a one-way hash of the original value, never the value:

```apex
Value_Hash__c = EncodingUtil.convertToHex(
    Crypto.generateDigest('SHA-256', Blob.valueOf(originalValue)))
```

That proves a specific value was present and erased, without retaining it. Record the
object, record Id, field name, action, timestamp, and hash — nothing else. And write
the audit row *before* the DML, so a failure mid-run leaves evidence of the attempt
rather than losing exactly the rows that failed.

---

## Gotcha 10: Some Records Cannot Be Deleted, and That Needs a Legal Position

**What happens:** A runbook promises complete erasure and then meets records that
cannot be removed — Setup Audit Trail entries, certain platform-managed history, and
data whose retention is required by a competing legal obligation (tax, financial
services record-keeping, anti-money-laundering).

**When it occurs:** During the first real request, when it becomes an urgent legal
question rather than a design decision.

**How to avoid:** Enumerate the exceptions during design, not during execution, and
get each one a written position from legal: what cannot be erased, why, under which
competing obligation, and what compensating control applies. Most privacy regimes
accommodate a competing legal obligation; none accommodate an unexplained residual
copy. The output is a documented residual-risk register, and it belongs in the same
folder as the runbook.

---

## Gotcha 11: The Deadline Is Measured Per Request, Under Load

**What happens:** A process is rehearsed once, takes forty minutes, and is signed off
against a thirty-day regulatory window. Then fifty requests arrive in a week following
a breach notification, and the process does not scale.

**When it occurs:** After any public incident, which is precisely when volume spikes
and when scrutiny is highest.

**How to avoid:** Measure the rehearsal's elapsed time per object and in total, then
model the volume you would see after an incident rather than in a normal month.
Automate the parts that are per-request rather than per-object, and know in advance
which steps are manual and how many people can execute them concurrently. A workflow
that meets the deadline at one request per week and fails at ten is not compliant, it
is untested.
