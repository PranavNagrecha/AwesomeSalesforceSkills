# Template — LWC Public API Contract

Use this template to document the public API of an LWC bundle as part of hardening it. Fill it in before (or while) writing the code so the contract drives the implementation, not the other way around.

---

## 1. Bundle identity

| Field | Value |
|---|---|
| Bundle | `force-app/main/default/lwc/<name>/` |
| Description | (one-sentence purpose; what role does this play on the page?) |
| Surfaces | `lightning__RecordPage` / `lightning__AppPage` / `lightning__FlowScreen` / `lightning__HomePage` / `lightningCommunity__Page` / programmatic |
| Bound SObject(s) | (e.g. `Account`, `Topic__c`, or "none — generic") |
| Form factors | `Large`, `Small`, both |

---

## 2. `@api` properties

For every `@api` property, fill in the row.

| Property (camelCase) | HTML attribute (kebab-case) | Required? | Type | Default | Coercion in setter? | Notes |
|---|---|---|---|---|---|---|
| `recordId` | `record-id` | YES | string Id (15/18) | n/a | string-guard in setter | Injected by record-page host; never assume non-string |
| `maxRows` | `max-rows` | NO | integer 1-50 | 5 | `Number()` + range clamp | Coerce App Builder string |
| `enabled` | `enabled` | NO | boolean | false | `v === true \|\| v === 'true'` | HTML attribute is always a string |

Rules:

- Required props must have a guard in `connectedCallback` (throw, log + early return, or fallback render).
- Optional props with a default must mirror the default in JS (the `default` in `<targetConfig>` is App-Builder-only).
- Every property whose value comes from HTML / App Builder / Flow needs a setter that coerces.

---

## 3. `@api` methods

For every `@api` method, fill in the row. **If the row's "Replaceable by event?" is YES, refactor instead of documenting.**

| Method | Arguments | Returns | Side effects | Idempotent? | Replaceable by event? | Notes |
|---|---|---|---|---|---|---|
| `focusInput()` | none | void | sets DOM focus | yes | NO (genuine imperative) | Used by parent on tab navigation |
| `refresh()` | none | Promise | re-runs wire | yes | YES — fire `<refreshrequest>` event from child instead | Refactor target |

Imperative-method criteria (keep as `@api` method): the action is one-shot, the result is a side effect on the DOM/state of the child, and the parent has no reason to "subscribe" to anything.

---

## 4. CustomEvents emitted

| Event name | When | `detail` shape | `bubbles` / `composed` | Notes |
|---|---|---|---|---|
| `topicchange` | user picks a topic | `{ topicId: string }` | true / true | crosses shadow boundary if needed |
| `savesuccess` | async save resolves | `{ recordId: string }` | true / false | parent wires via `onsavesuccess` |

Rules:

- Event names lowercase, no underscores or dashes.
- `detail` shape is part of the public contract — document it.
- Default to `bubbles: false, composed: false` unless you specifically need cross-boundary delivery.

---

## 5. `<targetConfig>` design properties (admin-facing)

For every `<property>` block in every `<targetConfig>`, fill in the row.

| Target | Property | Type | Default | Datasource / range | Notes |
|---|---|---|---|---|---|
| `lightning__RecordPage` | `maxRows` | Integer | 5 | min=1 max=50 | mirrored as JS default |
| `lightning__RecordPage` | `primaryField` | String | "Name" | datasource="Name,Industry,..." | fixed-set picker |
| `lightning__FlowScreen` | `initialTopic` | `{T extends SObject}` | n/a | propertyType="T" | Flow-only SObject input |

Rules:

- One `<targetConfig>` per target. Defaults do NOT cross targets.
- `propertyType` is Flow-only.
- For numeric fields, set `min`/`max`.
- For fixed-set strings, use `datasource="A,B,C"`.

---

## 6. Required-prop guard strategy

Pick one for the bundle:

- [ ] **Throw in `connectedCallback`** — visible, easy to debug. Acceptable for App Builder / record page; harsh on Flow screens.
- [ ] **Log + render fallback template** — best for Flow screens (Flow halts on uncaught errors).
- [ ] **Early return in `connectedCallback` + render placeholder** — acceptable for non-critical components.

Document the choice in the JSDoc on the class.

---

## 7. Verification

Confirm each item before considering the hardening done:

- [ ] Every `@api` property that can receive a string from HTML / App Builder has a setter that coerces.
- [ ] Every required `@api` property is validated in `connectedCallback`.
- [ ] No `@api` method exists that could be replaced with a CustomEvent.
- [ ] Every design `<property>` has explicit `type` and (where applicable) `default`, `datasource`, `min`, `max`.
- [ ] `propertyType` only appears inside `<lightning__FlowScreen>` `<targetConfig>` blocks.
- [ ] All boolean `@api` properties coerce string `"true"`/`"false"`.
- [ ] No setter mutates a backing field in place — every assignment is a reassignment.
- [ ] `python3 skills/lwc/lwc-public-api-hardening/scripts/check_lwc_public_api_hardening.py <bundle-path>` exits 0.
- [ ] Jest tests cover: missing required prop, string-from-HTML coercion, in-range / out-of-range numeric, boolean from string.
