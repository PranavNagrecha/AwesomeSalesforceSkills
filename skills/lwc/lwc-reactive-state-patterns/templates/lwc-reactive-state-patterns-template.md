# LWC Reactive State Audit — Work Template

Use this template when auditing or refactoring an LWC component for the
post–Spring '20 reactivity contract.

## Scope

**Skill:** `lwc-reactive-state-patterns`

**Component path:** `force-app/main/default/lwc/<componentName>/`

**API version (from js-meta.xml):** _______ (must be ≥ 48 for the rules
in SKILL.md to apply)

## Per-Field Audit

| Field | Type | Currently `@track`? | Needed? | Update style | Action |
|---|---|---|---|---|---|
| | primitive / object / array / Date/Set/Map / external | yes / no | yes / no | reassign / in-place / re-create | keep / drop @track / refactor |

(Add one row per reactive field. The decision rules:
- primitive → `@track` not needed
- object/array → if reassign, drop `@track`; if in-place mutation, keep
- Date/Set/Map → `@track` does NOT help; rewrite as re-create-and-reassign
- external instance → cannot be reactive; serialize to a primitive view)

## `renderedCallback` Audit

For each `renderedCallback` in the component:

- [ ] Does the body assign to `this.<reactiveField>`?
- [ ] If yes, is there a `_hasRenderedOnce` guard?
- [ ] Or a compare-then-set pattern (`if (current !== new) { current = new; }`)?
- [ ] If neither, this is an infinite-loop candidate — fix before merging.

## Expensive-Getter Audit

| Getter | Used in template? | Cost per call | Plan |
|---|---|---|---|
| | yes/no | O(1) / O(n) / O(n log n) | leave / cache via setter |

## Refactor Plan

(Specific lines/files to change.)

1.
2.
3.

## Verification

- [ ] All Jest specs still green.
- [ ] No unguarded `renderedCallback` writes remain.
- [ ] No `@track` on primitives or on fields updated only via reassignment.
- [ ] No Date/Set/Map in-place mutations.
- [ ] `apiVersion` declared explicitly in `js-meta.xml`.
- [ ] Manual smoke test in scratch org confirms the symptom that prompted the audit is gone.
