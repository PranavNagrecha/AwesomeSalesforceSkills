# Wire Service Review Template

Fill this in before writing the first `@wire`. Step 1 of the Recommended Workflow.

## Data Path

| Item | Value |
|---|---|
| Object(s) | |
| Supported by UI API? | Yes / No — if No, the read must be a cacheable Apex wire |
| Read source | UI API wire / Apex wire / GraphQL wire / base component |
| Wire form | Property (`foo.data`) / Function (`handler({data, error})`) |
| Reactive parameters (`$prop`) | |
| Sentinel for "not chosen yet" | `undefined` (wire must not fire) / `null` (wire fires, Apex handles it) |
| Field selection | `fields` list / `layoutTypes` + `modes` / `optionalFields` for may-not-see |
| Writes performed? | Yes / No — if Yes, which function |
| Caches invalidated by the write | Apex wire / UI API wire / GraphQL — list each |
| Refresh call per cache | `refreshApex(...)` / `notifyRecordUpdateAvailable([...])` / `refreshGraphQL(...)` |
| Copy boundary | Where the provisioned data is spread before transformation |

## Wired Apex Contract

| Method | Annotation | Mutates? | Wired or imperative |
|---|---|---|---|
| | `@AuraEnabled(cacheable=true)` / `@AuraEnabled` | | |

A method that mutates cannot be `cacheable=true`, and a method that is not `cacheable=true`
cannot be wired. If a row breaks that rule, the design is wrong, not the annotation.

## Rendered States

| State | Condition | Rendered as |
|---|---|---|
| Loading | no `data` **and** no `error` yet | |
| Empty | wire emitted, result is empty | |
| Error | `error` populated | |
| Ready | `data` populated | |

## Review Checklist

- [ ] Wire is used only for read/provisioning scenarios.
- [ ] Every wired Apex method is `cacheable=true` and non-mutating.
- [ ] Reactive parameters are defined intentionally; no `$` is nested in a collection.
- [ ] No reactive config property is assigned inside `renderedCallback()`.
- [ ] Wired data is copied before mutation, sorting, or annotation.
- [ ] Refresh behavior after writes is explicit, one call per cache, and never polled.
- [ ] Error handling matches the adapter shape (`error` vs `errors`; `body` array vs object).
- [ ] Loading, empty and error are three distinct states with a Jest case each.

## Notes

Document whether the component should remain wired, move to imperative access, or use LDS
base components instead — and record which caches a write invalidates, since that decision
is invisible in the code once the refresh calls are written.
