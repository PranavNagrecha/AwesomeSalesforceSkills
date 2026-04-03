# Custom Metadata In Apex Worksheet

## Configuration Decision

| Question | Answer |
|---|---|
| Is this app configuration or business data? | |
| Why is CMT better than labels or settings here? | |
| Package controlled or subscriber controlled? | |
| Read only or deployment updates required? | |

## Reader Design

- Metadata type:
- Record selection key:
- Default behavior if record missing:
- Reader service name:

## Guardrails

- [ ] No ordinary DML assumption on `__mdt`
- [ ] Tests state which metadata records they rely on
- [ ] Packaging visibility is understood
- [ ] Labels/settings were rejected for a real reason
