# LWC Error Boundaries — Work Template

## Scope

**Skill:** `lwc-error-boundaries`

**Request summary:** Describe the page or app, and what currently happens when one part of
it fails.

## Boundary map

One row per boundary. If a row's answer to the last column is "no", the boundary is too
high — see `references/gotchas.md`, Gotcha 2.

| `boundary-name` | Subtree it wraps | Error producers inside (UI API read / UI API write / Apex / network / none) | Can the user still do something useful if this disappears? |
|---|---|---|---|
| | | | |

## Answers to the Questions table

| Question | Answer |
|---|---|
| Retry meaningful for this failure? | |
| Telemetry target (custom object / external logger / none today) | |
| Ever placed on an Experience Cloud page? | |
| Apex throws `AuraHandledException`? | |
| Any programmatically attached handlers in the subtree? | |

## Normaliser branches exercised

Tick the shapes this build can actually receive; each ticked box needs a Jest fixture.

- [ ] UI API read — `error.body` is an array
- [ ] UI API write — object, possibly with `output.errors` / `output.fieldErrors`
- [ ] Apex — object
- [ ] Network / offline — object
- [ ] Native `Error` from `errorCallback` — no `body`

## Checklist

- [ ] One boundary per independently useful unit; none at the page root by default
- [ ] Boundary owns no wire adapter and no imperative call
- [ ] Fallback depends on nothing that can also fail
- [ ] `lwc:if` / `lwc:else`, no negated expressions in the template
- [ ] Telemetry call wrapped in its own `try/catch`
- [ ] No `body.stackTrace` and no `stack` string in rendered output
- [ ] Retry capped by `maxRetries`, or absent for deterministic failures
- [ ] `check_lwc_error_boundaries.py --manifest-dir <lwc dir>` reports zero ERROR
- [ ] Jest: one case per ticked normaliser branch, plus the throwing-child boundary case

## Notes
