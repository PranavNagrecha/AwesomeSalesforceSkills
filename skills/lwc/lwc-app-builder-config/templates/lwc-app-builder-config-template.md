# LWC App Builder Config — Surface × Property Worksheet

Fill this in before you open the `.js-meta.xml`. Every cell you leave blank becomes a default someone else chooses for you, and several of them cannot be changed once the component is placed.

**Skill:** `lwc-app-builder-config`

**Bundle name:** `___________________`  **Request summary:** _(what the requester actually asked for)_

---

## 1. Answers to the Questions to Ask

| Question | Answer |
|---|---|
| Which surfaces, and do they need the same knobs or different ones? | |
| For record pages, which objects — or is "all of them" the honest answer? | |
| Phone, desktop, or both, per surface? | |
| For each admin input: type, default, legal range? | (fill the matrix below) |
| Which inputs depend on org schema rather than a fixed list? | |
| Managed package or live Experience Cloud site? | |
| How will we know it is configured correctly before an admin finds out? | |

---

## 2. Surface × Property Matrix

Mark each cell with the property's configuration on that surface, or `—` if the property does not apply there.

| Property | Type | Record Page | App Page | Home Page | Utility Bar | Community Default |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

Per-surface settings that are not properties:

| Setting | Record Page | App Page | Home Page | Utility Bar | Community Default |
|---|---|---|---|---|---|
| `<objects>` (record pages only) | | n/a | n/a | n/a | n/a |
| Form factors (`Large` / `Small`) | | | `Large` only | | n/a |
| `event` + `schema` (App Page only) | n/a | | n/a | n/a | n/a |

Type reminders: App Builder targets take `Boolean` / `Integer` / `String` only; `Color` and `ContentReference` are Experience Cloud types; `min` / `max` apply to `Integer`; `datasource` and `placeholder` apply to `String`.

---

## 3. Irreversibility Review

Tick each one you have consciously decided, not defaulted.

- [ ] Object scope — an `<object>` cannot be removed once the component is placed on that object's record page.
- [ ] Form factors — the set can only grow after the component is in use.
- [ ] `min` / `max` — frozen once the component is on a Lightning page.
- [ ] Page-type support — cannot be withdrawn while in use on that page type.
- [ ] `required="true"` — cannot be added to a component already in a site or managed package.
- [ ] `isExposed` — in a released package it moves only from `false` to `true`.
- [ ] `actionType` (`lightning__RecordAction` only) — cannot change after deploy.

Anything unticked is a decision still owned by whoever types the XML. Push it back to the requester.

---

## 4. Apex Datasource (only if a property needs a schema-driven list)

| Question | Answer |
|---|---|
| Class name | |
| Does it need `DesignTimePageContext` (different list per object or page type)? | |
| How many values can it return, worst case? (>200 needs `setContainsAllRows(true)` and a server-side filter) | |
| Is the class in the same `package.xml` as the bundle? | |
| Test class name | |

---

## 5. Verification Plan

| Surface | What proves it works | Done |
|---|---|---|
| Setup → Lightning Components | label + description read well | |
| Each configured record-page object | component appears, knobs render | |
| One *unconfigured* object | component does **not** appear | |
| App Page | knob set differs from record page | |
| Home Page | no phone offer | |
| Experience Builder | in the panel, properties editable | |
| `check_lwc_app_builder_config.py --strict` | zero ERRORs | |
| Jest suite | defaults and setters pinned | |

---

## 6. Notes

Record any deviation from the standard pattern and the reason, especially a deliberate decision to leave a record-page target unscoped or a target without a `targetConfig`.
