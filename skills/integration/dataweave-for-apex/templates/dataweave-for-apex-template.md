# DataWeave for Apex — Work Template

Use this template when authoring or reviewing a DataWeave-for-Apex transformation.

## Scope

**Skill:** `dataweave-for-apex`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Source MIME type and a 3–5 record sample of the input:
- Target MIME type and required output shape:
- Caller context (sync REST class, Queueable, Batch, trigger):
- Calling class API version (53.0+ required, `apexdev.txt` 264 L26984; it also selects DataWeave 2.5 / 2.8 / 2.9, L26905–26908):
- Optional/missing-field policy (defaults? skip rows? throw?):

## Approach

- [ ] DataWeave-for-Apex is justified (field count, nesting, repeats) — verified against Decision Guidance
- [ ] Script deployed as `dw/<Name>.dwl` + `.dwl-meta.xml` (`DataWeaveResource`), not a static resource
- [ ] Apex caller hoists `createScript` outside any loop
- [ ] Every `as <Type>` paired with a `default` for nullable source paths
- [ ] XML namespaces declared explicitly when source uses prefixes

## Review Checklist

- [ ] Script header declares input MIME types matching every `execute` map key
- [ ] `System.DataWeaveScriptException` caught and its message logged
- [ ] Diagnostic logging includes `e.getMessage()` and a sanitized snippet of input
- [ ] Heap budget verified for representative input size (input × 4 + output)
- [ ] Tests cover golden path, empty input, malformed input, missing optional field, large input
- [ ] No inline script-as-String construction (`fromString`/`compile` not called)

## Notes

Record any deviations (unsupported MIME workarounds, MuleSoft alternative considered) and why.
