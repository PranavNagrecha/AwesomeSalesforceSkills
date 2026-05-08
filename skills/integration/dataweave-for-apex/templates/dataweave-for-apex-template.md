# DataWeave for Apex — Work Template

Use this template when authoring or reviewing a DataWeave-for-Apex transformation.

## Scope

**Skill:** `dataweave-for-apex`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Source MIME type and a 3–5 record sample of the input:
- Target MIME type and required output shape:
- Caller context (sync REST class, Queueable, Batch, trigger):
- Org API version (must be 61.0+ for GA DataWeave-for-Apex):
- Optional/missing-field policy (defaults? skip rows? throw?):

## Approach

- [ ] DataWeave-for-Apex is justified (field count, nesting, repeats) — verified against Decision Guidance
- [ ] Static resource registered with `cacheControl=Public` and `contentType=application/dw`
- [ ] Apex caller hoists `createScript` outside any loop
- [ ] Every `as <Type>` paired with a `default` for nullable source paths
- [ ] XML namespaces declared explicitly when source uses prefixes

## Review Checklist

- [ ] Script header declares input MIME types matching every `execute` map key
- [ ] `Dataweave.ExecuteException` and `Dataweave.ScriptException` caught separately
- [ ] Diagnostic logging includes `e.getMessage()` and a sanitized snippet of input
- [ ] Heap budget verified for representative input size (input × 4 + output)
- [ ] Tests cover golden path, empty input, malformed input, missing optional field, large input
- [ ] No inline script-as-String construction (`fromString`/`compile` not called)

## Notes

Record any deviations (unsupported MIME workarounds, MuleSoft alternative considered) and why.
