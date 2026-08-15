# Examples — Salesforce Shield Deployment

Salesforce Shield is three separately-licensed capabilities sold together:

> "Salesforce Shield is a trio of security tools that helps you build extra levels
> of trust, compliance, and governance right into your business-critical apps. It
> includes Shield Platform Encryption, Event Monitoring, and Field Audit Trail."
> — Salesforce Security Guide

They share a name and nothing else. They have different enablement paths, different
permissions, different failure modes, and different rollback stories. Deploying
"Shield" as one project is the root cause of most bad Shield rollouts.

---

## Example 1: Sequencing the three, and why the order is what it is

**Context:** An org buys Shield to satisfy a compliance programme with a deadline.

**Problem:** The instinct is to enable everything at once so the deadline is met.
Each capability then interferes with the diagnosis of the others: an encrypted field
breaks a report, and it is not obvious whether the cause is encryption, a Field Audit
Trail policy, or a transaction security policy that started blocking.

**Solution — three phases with a gate between each.**

```text
PHASE 1  Field Audit Trail
  Lowest risk, no query semantics change, and it starts accumulating history
  immediately - which matters because history is not retroactive.
  Gate: FieldHistoryArchive is populating; retention policy deployed.

PHASE 2  Event Monitoring
  Read-only observability. Nothing user-visible changes. Onboarding the log
  consumer is the long pole, and it is worth having in place BEFORE encryption
  changes anything - because it is what tells you what changed.
  Gate: an end-to-end incident rehearsal has been performed (Example 3).

PHASE 3  Shield Platform Encryption, one object at a time
  Highest risk: silently changes SOQL, report, and automation behaviour.
  Gate per object: query regression clean, re-encryption job complete,
  Encryption Statistics verified.
```

**Why this order:** Field Audit Trail's value is time-dependent, so starting it
first buys history you cannot buy later. Event Monitoring is the instrument you need
to observe the encryption rollout. Encryption is last because it is the only one of
the three that changes application behaviour.

**Why encryption is one object at a time:** enabling encryption on a field can
silently change what queries return. Batching six objects into one change means six
possible causes for every regression.

---

## Example 2: Field Audit Trail — the retention policy is metadata, and the numbers are smaller than you think

**Context:** A regulated org must retain field history for seven years.

**Problem:** Two claims circulate and both are wrong in ways that matter: that FAT
retains "up to 10 years," and that the retention policy is a Setup screen.

**The verified position.** Without Field Audit Trail:

> "When Field Audit Trail is turned off, Salesforce retains field history data for up
> to 18 months, and up to 24 months via the API."

With it:

> "With Field Audit Trail, you can track up to 200 fields per object, and Salesforce
> retains archived field history data until you delete it. ... Without Field Audit
> Trail, you can track only up to 20 fields per object."

So the retention story is **"until you delete it"** — not a fixed number of years.
The seven-year requirement is satisfied by *not deleting*, plus a documented deletion
process for when the obligation expires.

**The policy is Metadata API, not Setup:**

> "Use Salesforce Metadata API to define a field history retention policy for the
> fields that have history tracking enabled. Then use REST API, SOAP API, and Tooling
> API to work with your archived data. For information about enabling Field Audit
> Trail, contact your Salesforce representative."

```xml
<!-- objects/Account/Account.object-meta.xml (excerpt) -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <historyRetentionPolicy>
        <archiveAfterMonths>18</archiveAfterMonths>
        <archiveRetentionYears>7</archiveRetentionYears>
        <gracePeriodDays>30</gracePeriodDays>
        <description>Retain Account field history for 7 years per the
            records retention schedule. Owner: compliance@example.com</description>
    </historyRetentionPolicy>
</CustomObject>
```

Three field-level facts that change the design:

- `archiveAfterMonths` — "You can set a minimum of 1 month and a maximum of 18
  months. If you don't set a number, the default is 18 months." You cannot archive
  later than 18 months.
- `archiveRetentionYears` — "The number of years until you manually delete data from
  the archive. Use this field as a reminder for manually deleting data. **By default,
  field history data isn't automatically deleted when Field Audit Trail is
  enabled.**" It is a reminder field. Nothing deletes on your behalf.
- `gracePeriodDays` — extra time before the first archive, and "The
  `gracePeriodDays` interval applies only to the first time that the data is
  archived."

The component "is only available to users with the `RetainFieldHistory` permission."

**Defaults, if you deploy no policy:**

> "When Field Audit Trail is turned on, Salesforce relates `HistoryRetentionPolicy`
> automatically to the supported objects. By default, Salesforce archives data after
> 18 months in production, after one month in sandboxes, and stores all archived data
> until you delete it. Salesforce doesn't include the default retention policy when
> you retrieve the object's definition through Metadata API."

That last sentence explains a real confusion: a retrieve shows no policy on objects
that have one.

**What cannot be tracked at all**, regardless of licence:

> "Formula, roll-up summary, or auto-number fields; Created By and Last Modified By;
> Expected Revenue field on opportunities; Master Solution Title or the Master
> Solution Details fields on solutions; Long text fields; Multi-select fields."

If the compliance scope names a formula field, the answer is to track its inputs.

**Storage:** "Field history tracking data and Field Audit Trail data don't count
against your data storage limits." Costing FAT as a storage line item is a category
error.

---

## Example 3: Event Monitoring — rehearse the incident before you need it

**Context:** Event Monitoring is licensed and the log consumer is connected. The
programme is marked complete.

**Problem:** Nobody has ever answered a real question with it. The first attempt
happens during an incident, when the person asking discovers they do not know which
surface holds the answer, what the retention is, or what permission they need.

**The four surfaces, and what each is for:**

| Surface | Shape | Use it for |
|---|---|---|
| **Event Log File** | CSV files per event type per day | Bulk analysis, SIEM ingestion, historical questions |
| **Event Log Objects** | Queryable objects | "Unlike Event Log Files, which surface event data as CSV files, Event Log Objects allow querying of similar data via SOQL" |
| **Real-Time Event Monitoring** | Streaming objects (`LoginEventStream`, `LogoutEventStream`, …) | Detection and response within seconds |
| **Enhanced Transaction Security** | Policies with actions | Blocking or challenging in-flight |

The Security Guide's own comparison for a login question is instructive — the same
question has three different homes:

| | Real-Time Event Monitoring | Event Log Files | Login History |
|---|---|---|---|
| Object or file | `LoginEvent` | `EventLogFile` (Login event type) | `LoginHistory` |
| Permission | View Real-Time Event Monitoring Data | View Event Log Files | Manage Users |

Note the permissions differ. An analyst granted one cannot use the others.

**The rehearsal, as a scripted exercise:**

```text
Scenario: "User X may have exported customer data at 02:00 last Tuesday."

1. Who has the permission to answer this? Name them. If nobody does, that is
   the finding.
2. Pull the login: LoginHistory for the fast answer, LoginEvent or the Login
   EventLogFile for the detail. Note the Source IP AND the Forwarded for IP -
   the latter "doesn't get populated for OAuth and single sign-on logins."
3. Correlate with the report or API export event.
4. Cross-check Setup Audit Trail for configuration changes in the window.
5. Produce a timeline.
6. Record how long each step took and what was missing.
```

Step 6 is the deliverable. A rehearsal that produces a timeline proves the capability
exists; one that produces "step 3 took 40 minutes because nobody had the permission"
produces the backlog.

**Retention is the constraint people meet first.** Login History alone: "The Login
History page shows up to 20,000 records of user logins for the past 6 months. To see
more records, download the information to a CSV or GZIP file." Event log retention
varies by licence and event type. If the compliance requirement is measured in years,
the answer is a SIEM or a data lake, and that pipeline is part of the Shield
deployment — not a follow-on project.

---

## Example 4: The encryption phase, object by object

**Context:** Phase 3 begins with Contact.

**Problem:** Encryption changes query semantics silently. Nothing throws; queries
return fewer rows, reports come back empty, and automations stop firing.

**The per-object gate:**

```text
BEFORE
  1. Inventory every SOQL WHERE clause, report filter, list view filter,
     duplicate rule matching key, and automation criterion touching the
     candidate fields. The Platform Encryption Analyzer surfaces much of this;
     a repo grep finds the rest.
  2. For each, decide: drop the filter, switch the field to deterministic
     encryption, or do not encrypt that field.
  3. Snapshot the expected results of a representative set of queries and
     reports.

DURING
  4. Enable the policy for that object's fields only.
  5. Run the re-encryption job. Enabling a policy encrypts SUBSEQUENT writes;
     existing records stay in plaintext until this completes.

AFTER
  6. Verify on Encryption Statistics, per object.
  7. Re-run the snapshot from step 3 and diff. A row-count change with no
     error is the signature failure of this phase.
  8. Only then proceed to the next object.
```

**One interaction that catches Shield programmes specifically**, because it sits
across two of the three capabilities:

> "If you turn on Platform Encryption, the previously archived data remains
> unencrypted. For example, your organization uses Field Audit Trail to define a data
> history retention policy for an account field, such as the phone number field.
> After you turn on ..."
> — Salesforce Security Guide, *Field Audit Trail*

Archiving history first (Phase 1) and encrypting later (Phase 3) leaves the already
archived history unencrypted. That is a defensible position — the archive is a
separate store with its own controls — but it must be a *stated* position, because a
compliance reviewer who assumes encryption is universal will find it.

---

## Anti-Pattern: Buying Shield and never onboarding the logs

**What practitioners do:** license Shield for the encryption, enable Platform
Encryption, and leave Event Monitoring switched on but unconsumed. Event log files
accumulate; nobody downloads them; no policy references them.

**What goes wrong:** the org pays for a detection capability it does not have.
Detection requires someone looking, an alert path, and a retained history long enough
to answer questions about the past — and the retention windows are short by default.
When the incident arrives, the logs for the relevant period have aged out, and the
capability that would have caught it was present the whole time.

**Correct approach:** treat log consumer onboarding as a gating deliverable of the
Event Monitoring phase, not a follow-on. Name the destination, the retention period,
the alert conditions, and the person who receives them, and prove it end to end with
the incident rehearsal from Example 3 before the phase is closed.
