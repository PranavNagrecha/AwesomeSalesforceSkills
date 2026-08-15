# Gotchas — Salesforce Shield Deployment

Non-obvious behaviours encountered rolling out Shield's three capabilities.
Grounded in the Salesforce Security Guide and the Metadata API Developer Guide
(Summer '26, API 67.0).

## Gotcha 1: "Shield" Is Three Products, Not One Switch

**What happens:** A project plan says "enable Shield." There is no such action. Each
capability has its own enablement path, its own permissions, its own failure modes,
and its own rollback story — and when they are turned on together, each interferes
with the diagnosis of the others.

> "Salesforce Shield is a trio of security tools ... It includes Shield Platform
> Encryption, Event Monitoring, and Field Audit Trail."
> — Salesforce Security Guide

Field Audit Trail in particular is not self-service: "For information about enabling
Field Audit Trail, contact your Salesforce representative."

**When it occurs:** At project kickoff, in the plan, before anyone has looked at the
Setup screens.

**How to avoid:** Three phases, three gates. Field Audit Trail first (lowest risk,
and its value is time-dependent), Event Monitoring second (read-only, and it is the
instrument you need for phase three), Platform Encryption last and one object at a
time (the only one that changes application behaviour).

---

## Gotcha 2: Field Audit Trail Retention Is "Until You Delete It," Not Ten Years

**What happens:** A design document promises ten-year retention, citing a figure that
circulates widely. The actual mechanism is different in a way that changes the design.

Without FAT: "Salesforce retains field history data for up to 18 months, and up to 24
months via the API."

With FAT: "Salesforce retains archived field history data until you delete it."

And on the policy field itself: `archiveRetentionYears` is "The number of years until
you manually delete data from the archive. Use this field as a reminder for manually
deleting data. **By default, field history data isn't automatically deleted when Field
Audit Trail is enabled.**"

**When it occurs:** When a retention number is written into a compliance document
from a vendor summary rather than from the field reference.

**How to avoid:** State the mechanism, not a number: retention is unbounded until an
explicit deletion, and `archiveRetentionYears` is a reminder that deletes nothing.
That satisfies a seven-year or ten-year requirement — and it also means a
*maximum* retention obligation ("must not retain beyond N years") needs a deletion
process you build and schedule yourself.

---

## Gotcha 3: `archiveAfterMonths` Caps at 18 Months

**What happens:** A team tries to keep history in the live History related list for
two or three years before archiving, and the policy will not deploy.

> "`archiveAfterMonths` — Required. The number of months that you want to keep field
> history data in Salesforce before archiving. You can set a minimum of 1 month and a
> maximum of 18 months. If you don't set a number, the default is 18 months."

**When it occurs:** When "retention" and "archive delay" are conflated in
requirements gathering.

**How to avoid:** Separate the two questions. *Where* the data lives after N months
(the `FieldHistoryArchive` big object, queryable through a bounded SOQL subset) is
`archiveAfterMonths`, capped at 18. *How long* it is kept is unbounded and manual.
Note also that `gracePeriodDays` "applies only to the first time that the data is
archived," so it cannot be used to extend the window on an ongoing basis.

---

## Gotcha 4: The Default Retention Policy Is Invisible to Metadata Retrieve

**What happens:** A team retrieves object definitions to audit retention policies,
finds none, and concludes no policy is in effect. Data is being archived on a policy
they cannot see.

> "When Field Audit Trail is turned on, Salesforce relates `HistoryRetentionPolicy`
> automatically to the supported objects. By default, Salesforce archives data after
> 18 months in production, after one month in sandboxes, and stores all archived data
> until you delete it. Salesforce doesn't include the default retention policy when
> you retrieve the object's definition through Metadata API. Salesforce retrieves only
> custom retention policies with the object definition."

Note the sandbox default: **one month**, not 18. A sandbox will archive history
eleven times sooner than production, which makes sandbox behaviour a poor predictor.

**When it occurs:** During a compliance audit of "what is our retention policy," and
during any sandbox-based rehearsal.

**How to avoid:** Deploy an explicit `historyRetentionPolicy` on every in-scope
object, even where you are content with the default. An explicit policy is
retrievable, reviewable, and diffable; the default is none of those.

---

## Gotcha 5: Whole Field Categories Cannot Be History-Tracked

**What happens:** A compliance scope names a field that turns out to be untrackable,
and the gap is discovered at audit rather than at design.

> "You can't track these fields: Formula, roll-up summary, or auto-number fields;
> Created By and Last Modified By; Expected Revenue field on opportunities; Master
> Solution Title or the Master Solution Details fields on solutions; Long text
> fields; Multi-select fields."

Two more constraints from the same chapter that surprise people:

- "Salesforce tracks changes to fields with more than 255 characters as edited, and
  doesn't record their old and new values." So a 300-character text field is tracked,
  but uselessly for an audit that needs before-and-after values.
- "If Process Builder, an Apex trigger, or a Flow causes a change on an object that
  the current user doesn't have permission to edit, Salesforce doesn't track that
  change. Field history honors the permissions of the current user and doesn't record
  changes that occur in the system context." Automation-driven changes can therefore
  be invisible in field history — which is exactly the class of change an audit cares
  about.

**When it occurs:** When the compliance scope is written against a data dictionary
rather than against the tracking constraints.

**How to avoid:** Validate the scope field-by-field before committing to it. Where a
formula or roll-up is named, track its inputs instead. Where automation performs the
change, note that field history may not capture it and use Event Monitoring or a
custom audit object for that path.

---

## Gotcha 6: Field Audit Trail Data Does Not Count Against Storage — and Costing It Does

**What happens:** A programme is delayed by a storage-cost analysis for the archive.

> "Field history tracking data and Field Audit Trail data don't count against your
> data storage limits."
> — Salesforce Security Guide

**When it occurs:** During budgeting, where an archive naturally reads as a storage
line item.

**How to avoid:** Cost Field Audit Trail as a licence, not as storage. Track the
first copy's *duration* instead — "The first copy writes the field history that's
defined by your policy to archive storage and sometimes takes a long time. Subsequent
copies transfer only the changes since the last copy and are faster." That first copy
is the schedule risk.

---

## Gotcha 7: Deleting a Record Does Not Delete Its Archived History

**What happens:** A data subject deletion is executed, the records are gone, and the
archived field history retains the values.

> "If you delete a record in your production data, the delete cascades to the related
> history tracking records, but Salesforce doesn't delete the history copied into the
> `FieldHistoryArchive` big object."

**When it occurs:** During a right-to-be-forgotten workflow, and during any
data-destruction obligation — which is precisely where an overlooked copy is most
consequential.

**How to avoid:** Treat `FieldHistoryArchive` as a distinct store in every deletion
runbook, with its own explicit deletion step. Salesforce documents a separate
procedure for deleting data in `FieldHistoryArchive`; a deletion process that stops
at the record has not completed. See `security/customer-data-request-workflow`.

---

## Gotcha 8: Enabling Encryption Does Not Encrypt Already-Archived History

**What happens:** Field Audit Trail is enabled in phase one and Platform Encryption
in phase three. History archived in between is stored unencrypted, permanently.

> "If you turn on Platform Encryption, the previously archived data remains
> unencrypted. For example, your organization uses Field Audit Trail to define a data
> history retention policy for an account field, such as the phone number field. After
> you turn on ..."

**When it occurs:** In exactly the sequencing this skill recommends — which is still
the right sequencing, because the alternative (encrypt first) delays the start of
history accumulation and makes the encryption rollout harder to observe.

**How to avoid:** Make it a *stated* position rather than an accident. Record in the
compliance documentation that archived history written before the encryption date is
unencrypted, that it lives in a separate store with its own access controls, and what
compensating control covers it. A reviewer who assumes encryption is universal will
otherwise find it and treat it as a gap.

---

## Gotcha 9: The Same Question Has Three Homes, With Three Different Permissions

**What happens:** An analyst is granted Event Monitoring access and still cannot
answer a login question, or answers it from the wrong surface and reaches a wrong
conclusion about coverage.

The Security Guide's own comparison for a login question:

| | Real-Time Event Monitoring | Event Log Files | Login History |
|---|---|---|---|
| Object or file | `LoginEvent` | `EventLogFile` (Login event type) | `LoginHistory` |
| Permission | View Real-Time Event Monitoring Data | View Event Log Files | Manage Users |

**When it occurs:** During the first real investigation, when the permission gap
becomes the critical path.

**How to avoid:** Define the analyst persona explicitly and grant all three
permissions to it — they are not substitutes. Rehearse an investigation end to end
before closing the Event Monitoring phase, and treat "step N took 40 minutes because
nobody had the permission" as the deliverable of the rehearsal.

---

## Gotcha 10: Transaction Security's MFA Action Silently Becomes a Block

**What happens:** A transaction security policy is written with a multi-factor
authentication action, tested in the browser, and deployed. In the mobile app,
Lightning Experience, and every API path it blocks instead of challenging — and
nobody notices until an integration fails.

> "The multi-factor authentication action isn't available in the Salesforce mobile
> app, Lightning Experience, or via API for any events. Instead, the block action is
> used. For example, if a multi-factor authentication policy is triggered on a list
> view performed via the API, ..."
> — Salesforce Security Guide, *Enhanced Transaction Security*

**When it occurs:** As soon as the policy meets a non-browser surface, which for any
org with integrations is immediately.

**How to avoid:** Design MFA-action policies knowing the fallback is a hard block,
and test each policy against every surface the covered event can occur on —
Lightning, mobile, and API — not only the one where it was authored. Where a block is
unacceptable for an API path, scope the policy to exclude it rather than relying on a
challenge that will not appear.
