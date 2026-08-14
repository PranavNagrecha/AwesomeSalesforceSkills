# Salesforce Functions Replacement — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `salesforce-functions-replacement`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Before Starting questions from SKILL.md:

- Function name, runtime, and what it actually did:
- Invocation sites found in the org (Apex, trigger, Flow) — not just the project directory:
- Observed runtime and payload size, from real invocations:
- Why Functions was chosen originally (language, CPU, library, AI):

## Approach

Replacement target (Heroku, container, Apex, Agentforce Action) and — decided first — where the transaction boundary sits:

## Checklist

From the review checklist in SKILL.md, plus the failure modes in `references/gotchas.md`:

- [ ] Workload runtime checked against Heroku's non-configurable 30-second router timeout
- [ ] Callout budget checked against 120 s cumulative and 100 callouts per transaction
- [ ] If rewritten in Apex, the execution context gives 60,000 ms / 12 MB, not 10,000 ms / 6 MB
- [ ] Payload batched — one callout per transaction, never one per record
- [ ] Named Credential in place; no endpoint or secret in code
- [ ] Cutover and rollback documented for this workload alone

## Notes

Deviations from the standard pattern, and the reason for each:

