# Apex JSON Serialization — Work Template

Use this template when working on JSON serialization tasks in Apex.

## Scope

**Skill:** `apex-json-serialization`

**Request summary:** (fill in what the user asked for — serialize/deserialize, direction, shape known?)

## Context Gathered

Answer the Before Starting questions from SKILL.md:

- JSON direction (serialize / deserialize / both):
- JSON shape known at compile time? (yes → typed; no → untyped/streaming):
- Null fields in output: suppress / include / unknown:
- Payload size estimate (impacts heap strategy):
- External vs. internal data source (affects error handling strictness):

## Selected Approach

| Decision | Choice | Reason |
|---|---|---|
| Serialization method | `JSON.serialize` / `JSONGenerator` | |
| Null suppression | `true` / `false` | |
| Deserialization method | `JSON.deserialize` / `deserializeUntyped` / `JSONParser` | |
| Strict schema enforcement | `deserializeStrict` / no | |

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them:

- [ ] `suppressApexObjectNulls` (`true`) passed where null fields must be omitted
- [ ] `JSON.deserialize` wrapped in try/catch for `TypeException`
- [ ] `deserializeUntyped` result cast explicitly before use
- [ ] Static fields not expected in serialized output
- [ ] Large payloads sized against heap limit (6 MB sync / 12 MB async)
- [ ] `JSON.deserializeStrict` used where extra fields must be rejected

## Notes

Record any deviations from the standard pattern and why.
