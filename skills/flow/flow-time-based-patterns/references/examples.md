# Examples — Flow Time-Based Patterns

## Example 1 — "Reminder 2 days before SLA expiration, but only if case still open"

**Context.** Each Case has `SLA_Expiration_Time__c`. Owner should
get a reminder 2 days before — but only if the case is still open.
If the case closes before the reminder fires, the reminder must NOT
send.

**Wrong instinct.** Scheduled Path with `-2 days from
SLA_Expiration_Time__c`, no recheck.

**Why it's wrong.** Recheck-entry-condition is OFF by default. A
case that closes between queue time and execution time still gets
the reminder — irrelevant noise to the owner.

**Right answer.** Same Scheduled Path, but **enable
recheck-entry-condition** with criteria `Status != 'Closed'`. The
platform re-evaluates at execution time; closed cases silently exit
the path.

---

## Example 2 — Time-zone landmine: global team, "9 AM" Path

**Context.** Service Cloud org with reps in EMEA, Americas, APAC.
Record-triggered flow with a Scheduled Path "+1 day at 9 AM" sends
a follow-up reminder.

**What goes wrong.** Each user's saved record schedules in *that
user's* time zone. EMEA reps' records fire at 9 AM London. APAC
reps' records fire at 9 AM Tokyo. Stakeholder asked for "9 AM in
the customer's time zone" — neither.

**Right answer.** Two valid solutions:

- **(A)** Add a `Customer_Timezone__c` field to the record, populate
  on save based on customer location, store the desired fire time
  in UTC on a derived field, then schedule against that UTC field.
- **(B)** If "9 AM in the org's default TZ" is acceptable, move the
  logic to a **Scheduled Flow** that uses the org TZ regardless of
  the saving user.

The wrong answer is leaving the running-user TZ behavior unchallenged
because "it works in the demo".

---

## Example 3 — Wait element where it doesn't exist

**Context.** Admin tries to add a Wait element to a record-triggered
flow to "pause for 2 days then send email". They can't find the
Wait element in the toolbox.

**Why.** Wait elements are **autolaunched / orchestration only**.
Record-triggered flows can't have them.

**Right answer.** For record-triggered flows, use a **Scheduled
Path** off the trigger with `+2 days` offset. Same outcome,
different mechanism.

---

## Example 4 — Migrating a Workflow Rule with time-based action

**Context.** Classic Workflow Rule on Case: "if Priority = High and
Status != Closed, evaluate every time a record is created or
edited; queue a time-based action 4 hours later that emails the
manager." Migrating to Flow.

**Mapping.**

| Workflow concept | Flow equivalent |
|---|---|
| "Evaluate every time a record is created or edited" | Run when **created or updated** in record-triggered flow start |
| Criteria `Priority = High AND Status != Closed` | Entry conditions |
| Time-based action 4 hours | Scheduled Path `+4 hours` from trigger fire time |
| "Recheck the rule criteria" | Recheck entry condition on the Path |
| Send email field action | Send Email Action inside the Path |

**Common mistake.** Picking "Run when a record is created" only —
losing the "or updated" half of the original rule's behavior.

---

## Example 5 — Negative offset against past date fires immediately

**Context.** Scheduled Path "-2 days from `Promotion_End__c`". A
new Promotion record is created on Aug 5 with `Promotion_End__c =
Aug 1` (in the past). Admin expects nothing happens.

**What actually happens.** The Path fires **immediately** — the
platform considers the scheduled time (Jul 30) already past.

**Right answer.** Add an entry-condition check
`Promotion_End__c >= TODAY` so past-dated promotions don't enter the
flow at all. Or, in the Path body, check the date again and exit if
past.

---

## Anti-Pattern: Scheduled Path with no recheck on a long-lived record

```
Trigger: Case create or edit
Scheduled Path: +30 days from CreatedDate
  body: send "30-day check-in" email to owner
```

**What goes wrong.** The case may be closed, reassigned, or merged
into another case in those 30 days. Without recheck, the email goes
out anyway — to the wrong owner, on a closed case, on a record that
no longer represents the work.

**Correct.** Recheck entry condition: `Status != 'Closed' AND OwnerId
!= NULL AND IsDeleted = FALSE`. Reassignment is captured naturally
because the path runs as the *current* owner at execution time.
