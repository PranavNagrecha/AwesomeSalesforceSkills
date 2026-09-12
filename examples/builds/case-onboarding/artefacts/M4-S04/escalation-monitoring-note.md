# Monitoring note — how we will know next month that `Case_SLA_Escalation` still fires

Declared output of `M4-S04`. Written by `agents/metadata-builder`. Nothing here is deployable
metadata; it is the handover a human owns after activation.

Answers **Q91** — *"A saved report on escalated, still-open Cases, reviewed weekly by the Tier 2
lead."* Shape taken from `skills/admin/escalation-rules/references/metadata-examples.md`
§ "Verification and monitoring".

---

## 1. Why this note exists rather than being folded into the runbook

`Case.IsEscalated` is a plain writable boolean with `Create`, `Update`, `Filter`, `Group` and
`Sort` properties — not an engine-owned lock (`references/gotchas.md` #11). Anything with update
access can set or clear it: a data load, a Flow, an integration user, or an agent with the field
on the layout. Two consequences shape everything below:

1. Nothing reports on a rule that has quietly stopped firing. Silence looks identical to
   compliance.
2. A count of `IsEscalated = true` is **evidence of an escalation report, not proof of an
   escalation event**. Do not present it to Acme as "the rule fired N times".

---

## 2. The saved report to build at activation

| Report property | Value |
|---|---|
| Report type | Cases |
| Filters | `Escalated = True` **AND** `Closed = False` **AND** `Date/Time Opened = LAST 30 DAYS` |
| Grouping | Case Owner, then Priority |
| Columns | Case Number, Priority, Status, Date/Time Opened, Last Modified Date, Business Hours, Severity |
| Schedule | Weekly |
| Owner | **Tier 2 lead** (Q91). The individual is **OPEN** — Q91 names the role, not a person |
| Cadence | Weekly (Q91) |

`Severity` is added to the column list beyond the skill's standing definition because this build's
rule splits on `Case.Severity__c`: without it, a reviewer cannot tell which of the two entries a
row came from, and entry 1 is the one with no holiday pause (runbook § 4, R5).

**This report is not built as metadata by this step.** `plan.json` `steps[M4-S04].outputs[]`
declares no `Report` or `ReportFolder`, and `standards/build-orchestration.md` § 4 files reports
under a `ui` step. It is a handover instruction, not an artefact.

## 3. The equivalent queries, for a reviewer who wants the number before the report exists

Verbatim from `references/metadata-examples.md`. Aggregate, by owner:

```sql
SELECT OwnerId, COUNT(Id) escalatedOpen
FROM Case
WHERE IsEscalated = true AND IsClosed = false
GROUP BY OwnerId
ORDER BY COUNT(Id) DESC
```

Case-level, for spotting a wave or a tier that never fires:

```sql
SELECT Id, CaseNumber, Priority, Status, OwnerId, BusinessHoursId,
       CreatedDate, LastModifiedDate
FROM Case
WHERE IsEscalated = true AND IsClosed = false
  AND CreatedDate = LAST_N_DAYS:7
ORDER BY CreatedDate
```

`BusinessHoursId` is in the second query's column list for a reason specific to this build: a row
with a null `BusinessHoursId` is a case entry 2 measured on an unverified clock (runbook § 4, R1).

---

## 4. What the weekly review actually looks at

| Signal | What it means | First thing to read |
|---|---|---|
| Count is **zero** for a full week | Either nothing breached (good) or the rule stopped (bad). These are indistinguishable from the count alone | `gotchas.md` in order: engine batching, then criteria mismatch, then the calendar |
| Rows owned by `Tier_1_General` or `Billing` | The timer fired the notification but the reassignment did not land, **or** the row was escalated by something other than this rule | Owner-change history on the case; `owner-writer-map.md` § 1 |
| Rows with a null `BusinessHoursId` | Entry 2 ran on an unverified clock | Runbook § 4, R1 — is `M4-S03` deployed? |
| A new case created at `billing@acme.example` shortly after an escalation | The R2 mail loop is live | Runbook § 4, R2 |
| Count spikes right after a deploy | Cases already past 480 minutes escalated on the first pass | The step-4 baseline in the runbook |

Corroborate any count with owner-change history or `LastModifiedDate` movement at the expected
threshold before treating it as a firing count (`gotchas.md` #11).

---

## 5. Annual item, so it is not discovered in January

Holidays attached to a calendar suspend the escalation rules that use it (`gotchas.md` #10), and
an expired holiday list changes SLA behaviour in the *opposite* direction to what everyone
expects — escalations that used to pause start firing. Entry 2 reads whatever calendar
`Case.BusinessHoursId` names, so it inherits `M4-S01`'s holiday maintenance obligation
(`artefacts/M4-S01/holiday-maintenance-runbook.md` § 4, owned by Service Operations, one deploy
each Q4, individual owner **OPEN** per `decisions.md` **D-M4S01-02**).

Entry 1 is `businessHoursSource` `None` and observes **no** holidays at all. That is deliberate
and it is listed here so the annual review does not "fix" it.
