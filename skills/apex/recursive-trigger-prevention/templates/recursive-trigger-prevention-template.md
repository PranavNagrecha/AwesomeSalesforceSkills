# Recursion Guard Worksheet

## Recursion Source

| Item | Value |
|---|---|
| Object and event | |
| Self-DML, cross-object, or surrounding automation? | |
| Legitimate re-entry exists? | Yes / No |
| Guard granularity | Global / Record-aware / Delta-only |

## Candidate Guard

- Delta check:
- Record key or state key:
- Where guard runs:
- What should still be allowed:

## Guardrails

- [ ] Not a single global Boolean unless truly justified
- [ ] Multiple records in one transaction are handled safely
- [ ] Legitimate re-entry is preserved
- [ ] Guard sits before the recursive branch
