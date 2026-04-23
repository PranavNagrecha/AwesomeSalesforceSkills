---
name: lwc-conditional-rendering
description: "Use when writing, reviewing, or migrating Lightning Web Component templates that branch between UI states with `lwc:if`, `lwc:elseif`, and `lwc:else`, including getter-backed booleans, loading/error/ready state machines, keep-state vs reset-state toggles, and legacy `if:true` / `if:false` cleanup. Triggers: 'lwc:if vs if:true', 'lwc:elseif not working', 'conditional rendering in lwc', 'complex boolean in template'. NOT for choosing between component types at runtime — that is `lwc-dynamic-components` — and NOT for list rendering, which uses `for:each` or `iterator:it`."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "lwc:if vs if:true difference and when to migrate"
  - "lwc:elseif not working or throws a parse error"
  - "conditional rendering lwc best practice 2025"
  - "should i migrate if:true to lwc:if on existing components"
  - "complex boolean expression in lwc template like a && b || c"
  - "renderedcallback fires twice on lwc:if branch toggle"
  - "lwc:ref undefined inside conditional block"
tags:
  - lwc-conditional-rendering
  - lwc-if
  - lwc-else
  - lwc-elseif
  - directives
  - template-syntax
inputs:
  - "current branch structure — how many mutually exclusive UI states exist and how they are expressed today"
  - "data shape controlling visibility — which properties drive the branch and whether their update is reactive"
  - "performance or lifecycle concerns — whether branches re-mount vs stay mounted, and whether child state must survive a toggle"
  - "legacy `if:true` / `if:false` usage in the existing template that needs migration"
outputs:
  - "template using `lwc:if` / `lwc:elseif` / `lwc:else` with getter-backed computed booleans"
  - "decision on `lwc:if` (re-mount, reset state) vs CSS hide (keep state) for each toggle"
  - "checker report flagging legacy `if:true`, orphan `lwc:elseif`, complex template expressions, or `lwc:else={...}` errors"
  - "migration notes for converting chained `if:true` / `if:false` to the modern directive trio"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# LWC Conditional Rendering

Use this skill when a Lightning Web Component template must branch between UI states — loading vs ready, permitted vs denied, empty vs list, step 1 vs step 2 — or when a legacy template still uses `if:true` / `if:false` and needs to be migrated to the modern `lwc:if` / `lwc:elseif` / `lwc:else` trio. It activates on questions about evaluation rules, getter-backed booleans, lifecycle interactions with `renderedCallback` and `lwc:ref`, and the idiom for complex boolean logic.

---

## Before Starting

Gather this context before writing or migrating conditional markup:

- How many mutually exclusive branches are there today, and are they truly exclusive or just coincidentally non-overlapping?
- Is the property controlling the branch already reactive (a `@api`, `@track`ed, or wire-provisioned value), or is it derived from other state?
- When the branch changes, must any child state survive the toggle (form input, scroll position, focused cell)? That dictates `lwc:if` (re-mount) vs CSS hide (keep state).
- Is this template still on legacy `if:true` / `if:false`, and is there a chained pattern (`if:true`, then sibling `if:false` for the else case) that should become `lwc:if` / `lwc:else`?

---

## Core Concepts

Modern conditional rendering in LWC uses three cooperating directives, getters for anything that is not a single boolean, and a mount/unmount model — not a hide/show model.

### The Directive Trio: `lwc:if`, `lwc:elseif`, `lwc:else`

`lwc:if={prop}` evaluates the expression and, when the result is truthy, renders the element and its subtree. `lwc:elseif={other}` must immediately follow a sibling `lwc:if` or another `lwc:elseif` and is evaluated only when the preceding branch was falsy. `lwc:else` has no expression — `lwc:else={foo}` is a parse-time error — and it matches whatever remains. The expression inside `lwc:if` / `lwc:elseif` is not a reactive watch: reactivity comes from the underlying property (or getter dependency), not from the directive itself. The directive simply re-evaluates on the next rerender.

### Getters Are The Idiom For Computed Booleans

Template expressions in LWC are intentionally limited. You cannot write `lwc:if={a && b}`, `lwc:if={status !== 'error'}`, or `lwc:if={items.length > 0}`. Put computed logic in a JavaScript getter and reference the getter: `get isReady() { return this.status === 'done' && !this.error; }`, then `lwc:if={isReady}`. Getters compose cleanly, are unit-testable, and keep the template readable. Inverting a condition should use `lwc:else` rather than a negated getter when the negation exists only to flip a single branch.

### Branches Mount And Unmount — They Do Not Hide

When `lwc:if` flips from true to false, the DOM subtree is removed — not hidden. Child component instances are destroyed, internal state is lost, `disconnectedCallback` fires, and `lwc:ref` to anything inside that subtree becomes undefined. When the branch flips back, a fresh instance is created and `renderedCallback` fires again, so any side-effect code there must be idempotent. If the UX needs to hide a panel while preserving its state (open filter drawer, partially filled form), use CSS `display:none` or a class toggle instead. Branches also form their own sub-trees for slot assignment: a slotted element lives inside exactly one branch at a time.

### Legacy `if:true` / `if:false` Still Work — But Are Discouraged

`if:true={prop}` and `if:false={prop}` are the pre-`lwc:if` API. Salesforce's current guidance says they are no longer recommended, may be removed in the future, and are less performant in chained conditions because they do not share the `lwc:if` / `lwc:elseif` short-circuit. Migrating is straightforward and the skill's checker flags every instance.

---

## Common Patterns

### Loading / Error / Ready State Machine

**When to use:** A component fetches data and needs to show a spinner, an error card, or the ready view — exactly one at a time.

**How it works:** Expose a `status` property (`'loading' | 'error' | 'ready'`). Back each state with a getter (`isLoading`, `isError`, `isReady`). In the template chain `lwc:if={isLoading}` → `lwc:elseif={isError}` → `lwc:else` for the ready branch. The `lwc:else` block has no expression.

**Why not the alternative:** Three parallel `lwc:if` blocks rely on the JS to guarantee mutual exclusion, so a bug can render two branches at once. The chained directives make the exclusivity a template-level invariant.

### Keep-State Toggle vs Reset-State Toggle

**When to use:** A panel or drawer opens and closes via a button. Whether to use `lwc:if` or a CSS class depends on whether the user expects their partial state to survive.

**How it works:** For "reset every time" (confirmation modals, wizards that restart), use `lwc:if={isOpen}` — the subtree is fresh on every open. For "preserve my input" (filter drawers, collapsed sections), keep the component mounted and toggle `display:none` via a computed class getter. Document the choice in a comment so future edits do not regress it.

**Why not the alternative:** Blindly using `lwc:if` for a drawer destroys in-progress user input; blindly using CSS hide means stale state leaks between opens.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple show/hide of one element | `lwc:if={flag}` | Simplest primitive; re-mount is usually desirable |
| Two mutually exclusive branches | `lwc:if` + `lwc:else` | Encodes the exclusivity in the template |
| Three or more mutually exclusive branches | `lwc:if` + `lwc:elseif` + `lwc:else` | Short-circuits and avoids parallel `lwc:if` bugs |
| Boolean depends on multiple properties | Getter that returns a boolean | Template expressions are intentionally limited |
| Panel must preserve in-progress state across toggles | CSS `display:none` via class getter | `lwc:if` re-mounts and loses child state |
| Existing template uses chained `if:true` / `if:false` | Migrate to `lwc:if` / `lwc:elseif` / `lwc:else` | Legacy path is slower and officially discouraged |

---

## Recommended Workflow

1. **Inventory the branches** — list every UI state the component can show, confirm mutual exclusivity, and map each state to a property or getter.
2. **Decide mount vs hide** — for each toggle, ask whether child state must survive. Pick `lwc:if` for reset, CSS hide for preserve.
3. **Move logic into getters** — any boolean that is not already a single property becomes a getter with a descriptive name (`isReady`, `canEdit`).
4. **Write the chain** — use `lwc:if` + `lwc:elseif` + `lwc:else` for exclusive branches; use standalone `lwc:if` for independent toggles.
5. **Check lifecycle assumptions** — verify `renderedCallback` inside branches is idempotent and that no `connectedCallback` reaches into a `lwc:ref` that may not exist.
6. **Run the checker** — `python3 scripts/check_lwc_conditional_rendering.py --lwc-dir force-app/main/default/lwc` flags legacy directives, orphan `lwc:elseif`, expressions in `lwc:if`, and `lwc:else={...}` errors.
7. **Migrate legacy** — replace every flagged `if:true` / `if:false` with the modern trio in the same PR so the checker stays green.

---

## Review Checklist

- [ ] No `if:true` or `if:false` remains in any touched template.
- [ ] Every `lwc:elseif` immediately follows a sibling `lwc:if` or another `lwc:elseif`.
- [ ] `lwc:else` appears with no expression.
- [ ] No template expression contains `&&`, `||`, `!==`, `>`, `<`, or `.length` — those live in getters.
- [ ] Any `lwc:ref` accessed from JS is null-checked when the referenced element is inside a conditional branch.
- [ ] `renderedCallback` inside conditional subtrees is idempotent (guarded with `this._rendered` or equivalent).
- [ ] Toggles that must preserve child state use CSS `display:none`, not `lwc:if`.

---

## Salesforce-Specific Gotchas

1. **`lwc:if` unmounts — it does not hide** — Flipping to false destroys the subtree, fires `disconnectedCallback`, and voids any `lwc:ref` pointing inside. A user's partially filled input is lost unless the parent lifts the state up.
2. **`renderedCallback` fires again on re-entry** — Every time the branch flips back to true, a fresh instance is created and `renderedCallback` runs again. Side-effect code (third-party libs, focus(), one-time measurement) must be guarded for idempotency.
3. **`lwc:else={foo}` is a parse-time error** — `lwc:else` takes no expression. Authors migrating from other frameworks frequently try to add one.
4. **`lwc:elseif` must be a sibling following `lwc:if`** — Wrapping the `lwc:if` in a `<div>` and putting `lwc:elseif` outside that `<div>` breaks the chain; the `lwc:elseif` becomes orphaned and throws at compile time.
5. **Complex expressions inside `lwc:if` do not compile** — `lwc:if={a && b}` is not valid. Put the logic in a getter. This is intentional — templates stay declarative and testable.
6. **Legacy `if:true` / `if:false` are on a removal path** — They still compile, but Salesforce's own docs call them "no longer recommended" and flag them as less performant in chained conditions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Updated template | `lwc:if` / `lwc:elseif` / `lwc:else` chain with getter-backed booleans |
| Migration notes | Before/after snippets converting `if:true` / `if:false` to the modern trio |
| Checker report | File-and-line findings for legacy directives, orphan `lwc:elseif`, complex expressions, and `lwc:else={...}` errors |

---

## Related Skills

- `lwc/lwc-performance` — use when the core issue is rerender cost, list size, or lazy instantiation beyond the single-branch toggle.
- `lwc/lwc-dynamic-components` — use when the runtime choice is which component class to instantiate, not which sub-tree to render.
- `lwc/lwc-template-refs` — use when the focus is `lwc:ref` correctness, especially across mount/unmount boundaries created by `lwc:if`.
