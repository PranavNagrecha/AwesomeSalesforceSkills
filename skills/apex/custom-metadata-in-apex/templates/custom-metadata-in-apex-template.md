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

## Field Sheet

One row per field. Fill it before writing any `.field-meta.xml`.

| Field API name | Type | Longest value it can hold | Read path (`getAll` / `getInstance` / SOQL) | `fieldManageability` | Why not the default |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

- Any field whose longest value can exceed 255 characters must say **SOQL** — the cache accessors truncate there.
- `fieldManageability` is one-way for `SubscriberControlled`: the publisher can never correct it in an upgrade.

## Write Path

- [ ] No runtime write is needed — skip the rest of this section.
- [ ] Deployer class name:
- [ ] `DeployCallback` class name:
- [ ] What the callback does on `Succeeded`:
- [ ] What it does on `SucceededPartial`:
- [ ] What it does on `Failed` / `Canceled`:
- [ ] Where the job Id is persisted, if a UI must poll:
- [ ] `Test.isRunningTest()` guard is in place before `enqueueDeployment`:

## Packaging

| Question | Answer |
|---|---|
| Type `visibility` (`Public` / `Protected` / `PackageProtected`) | |
| Per-record `protected` value, and why | |
| Namespace this will ship under (blank if unpackaged) | |
| `fullName` format the deployer builds | |

## Guardrails

- [ ] No ordinary DML assumption on `__mdt`
- [ ] Tests state which metadata records they rely on
- [ ] Packaging visibility is understood
- [ ] Labels/settings were rejected for a real reason
- [ ] A fallback record is deployed and asserted by a test
- [ ] `python3 scripts/check_custom_metadata_in_apex.py --manifest-dir <src>` reports no findings
