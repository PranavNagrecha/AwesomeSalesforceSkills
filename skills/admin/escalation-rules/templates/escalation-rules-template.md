# Escalation Rules — Configuration Template

Fill this in **before** writing XML. Every column maps to an element in
`escalationRules/<Object>.escalationRules-meta.xml`; the element name is given in the
"Metadata" column so the design and the deploy cannot drift apart.

Shape the file from `references/metadata-examples.md`, then lint it with:

```bash
python3 skills/admin/escalation-rules/scripts/check_escalation_rules.py \
  --manifest-dir force-app/main/default
```

---

## Escalation Rule Summary

| Property | Metadata | Value |
|---|---|---|
| Rule Name (developer name) | `escalationRule/fullName` | |
| Active on deploy? | `escalationRule/active` | `false` for the parallel run, `true` only at cutover |
| Object | file name | Case |
| Rule this one replaces (if any) | — | |
| Incumbent rule's owner / sign-off | — | |
| Cutover window | — | |

Only one rule in the file should carry `active` = `true`. The checker errors on two.

---

## Rule Entries

Entries are evaluated top to bottom and the **first match wins**, so number them
from most specific to catch-all. Duplicate this block per entry.

### Entry 1

| Property | Metadata | Value |
|---|---|---|
| Entry order | position in file | 1 |
| Criteria | `criteriaItems` (`field` / `operation` / `value`) | e.g. `Case.Priority` `equals` `Sev-1` |
| …or formula (never both) | `formula` | |
| Filter logic across criteria | `booleanFilter` | e.g. `1 AND (2 OR 3)`; blank = all ANDed |
| Clock source | `businessHoursSource` | `None` (24/7) / `Case` / `Static` |
| Named calendar (only when Static) | `businessHours` | |
| Clock start | `escalationStartTime` | `CaseCreation` / `CaseLastModified` |
| Edit ends escalation? | `disableEscalationWhenModified` | `true` / `false` |

Record **why** for the last three rows — they are the two levers most often confused
(`references/gotchas.md` Gotchas 6 and 7):

- Clock source chosen because: 
- Clock start chosen because: 
- Edit behaviour chosen because: 

**Escalation Actions** — stages live inside this entry, not in sibling entries.
Convert hours to minutes here so the transcription error in Gotcha 8 is visible:

| Stage | SLA agreed (hours) | `minutesToEscalation` (hours × 60) | Notify (`notifyTo` / `notifyEmail` / `notifyCaseOwner`) | Reassign (`assignedTo`) | `assignedToType` | Template (`notifyToTemplate` / `assignedToTemplate`) |
|---|---|---|---|---|---|---|
| 1 | | | | (blank = notify only) | `User` / `Queue` | |
| 2 | | | | | | |
| 3 | | | | | | |

Any stage with a value in the Reassign column writes `OwnerId`. List the automation
that will re-fire because of it:

- 

### Entry 2 (duplicate the block above per entry)

| Property | Metadata | Value |
|---|---|---|
| Entry order | position in file | 2 |
| Criteria | `criteriaItems` | |
| Clock source | `businessHoursSource` | |
| Named calendar (only when Static) | `businessHours` | |
| Clock start | `escalationStartTime` | |
| Edit ends escalation? | `disableEscalationWhenModified` | |

---

## Calendars Referenced

Design and maintenance of the calendars themselves belongs to
`admin/business-hours-and-holidays`; record here only which entries read which calendar.

| Calendar name | Time zone | Read by which entries | Holidays maintained by | Next review |
|---|---|---|---|---|
| | | | | |

Entries with `businessHoursSource` = `None` observe **no** calendar and **no** holidays.
List them explicitly so the exception is a decision, not an oversight:

- 

---

## Targets to Pre-Create in the Target Org

| Type | Developer name | Exists in target? |
|---|---|---|
| Queue | | |
| User | | |
| Classic email template | | |
| Business hours calendar | | |

---

## Monitoring Handover

| Property | Value |
|---|---|
| Report or query | e.g. Cases where `Escalated = True` AND `Closed = False` |
| Owner | |
| Cadence | |
| Baseline taken before cutover (count / date) | |

---

## Validation Checklist

- [ ] Exactly one rule in the file has `active` = `true`, and it is the intended one
- [ ] Entries are ordered most-specific first; any catch-all entry is last
- [ ] No entry sets both `criteriaItems` and `formula`
- [ ] Every `minutesToEscalation` was derived by multiplying the agreed hours by 60
- [ ] `businessHours` is present exactly when `businessHoursSource` is `Static`
- [ ] `escalationStartTime` and `disableEscalationWhenModified` were chosen with a reason recorded
- [ ] Every action with `assignedTo` also sets `assignedToType`
- [ ] All queues, users, calendars and Classic templates exist in the target org
- [ ] Automation that watches `OwnerId` was reviewed for each reassigning stage
- [ ] `scripts/check_escalation_rules.py` reports zero ERROR findings, and every WARN was read and accepted
- [ ] The after-hours clock test was run (`admin/business-hours-and-holidays`, Example 4)
- [ ] Cutover was deploy-inactive then activate, with the baseline count captured first

---

## Notes

(Record deviations from standard patterns, special case criteria, stakeholder decisions,
and anything the checker flagged that was accepted knowingly.)
