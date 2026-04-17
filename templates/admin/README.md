# Admin Templates

Canonical patterns for the Salesforce admin surface — Setup, Object Manager, Permission Sets, Validation Rules. Referenced by the Tier-1 / Tier-2 run-time admin agents (`object-designer`, `permission-set-architect`, `validation-rule-auditor`, `field-impact-analyzer`, etc.).

These are not deployable metadata files. They are the formulas a senior admin or architect runs mentally when they design the real thing. Each agent reads the relevant template at the start of its Plan and produces Setup-ready output that conforms.

## Contents

| File | Purpose | Used by |
|---|---|---|
| [`naming-conventions.md`](./naming-conventions.md) | Reserved words, prefixes, casing, reserved-word checks for every metadata type | `object-designer`, `field-impact-analyzer`, `csv-to-object-mapper` |
| [`permission-set-patterns.md`](./permission-set-patterns.md) | Profile-less architecture: PS vs PSG vs muting PS, persona → PS mapping, session-based and time-limited assignment | `permission-set-architect`, `sharing-audit-agent` |
| [`validation-rule-patterns.md`](./validation-rule-patterns.md) | Bulk-safe VR shapes, integration bypass, IsChanged vs ISNEW framing, VR + Flow coexistence | `validation-rule-auditor`, `data-loader-pre-flight` |

## Authoring rules

- Every template cites its source skills in its own footer.
- Every template has a "What the agent should do with this" section so the agent's Plan has a clear handoff.
- Templates must be update-safe — if a Salesforce release changes the recommended shape, the template is updated and every citing agent inherits automatically.
