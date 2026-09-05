# Recursion Guard Worksheet

Fill this in before writing a guard. Each row corresponds to a question in the
`## Questions to Ask Before Configuring` table in SKILL.md.

## Recursion Source

| Item | Value |
|---|---|
| Object and event | |
| Self-DML, cross-object, or surrounding automation? | |
| Row count of the DML that re-enters (above or below 200)? | |
| All-or-none DML, or `allOrNone = false` / API partial success? | |
| Legitimate re-entry exists? | Yes / No |
| Guard granularity | Global / Record-aware / Record + fingerprint / Delta-only |

## Observed Invocation Counts

From `sf apex tail log` — see `references/examples.md`, Example 3.

| Trigger and event | Count before fix | Count after fix | Expected |
|---|---:|---:|---|
| | | | 1 = no re-entry; 2 = workflow field update re-fire; 3+ = loop |
| | | | |

## Candidate Guard

- Delta check (fields compared against `Trigger.oldMap`):
- Record key:
- Fingerprint fields (exactly what the handler reads):
- Context key (`Trigger.operationType` value(s) scoped):
- Where guard runs (which method, before which DML):
- What should still be allowed through:

## Data-Load Route

- Bypass mechanism chosen: `TriggerControl_BypassAll` Custom Permission / `Trigger_Setting__mdt` record
- Who or what is bypassed:
- When it is switched back on, and who verifies:

## Guardrails

- [ ] Not a single global Boolean unless truly justified
- [ ] Multiple records in one transaction are handled safely
- [ ] More than 200 records in one DML are handled safely (guard is not one-shot)
- [ ] Legitimate re-entry is preserved
- [ ] Guard sits before the recursive branch
- [ ] Guard has a `@TestVisible` reset hook
- [ ] Bulk test at 400+ records asserts each record processed exactly once
- [ ] Data loads use the bypass, not the guard
- [ ] `python3 scripts/check_recursive_trigger_prevention.py --manifest-dir <src>` reports no ERROR
