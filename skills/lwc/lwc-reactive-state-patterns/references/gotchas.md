# Gotchas — LWC Reactive State Patterns

Non-obvious behaviors of the LWC reactivity system that cause real
production problems. Each entry is **what / when / how**.

## 1. `@track` does not make Date / Set / Map reactive

**What:** The reactivity proxy only observes plain objects and arrays.
Date, Set, Map (and any class instance with internal mutability) are
silently NOT proxied. Calling `.add()` / `.set(k,v)` / `.setHours()`
on a `@track`-decorated field does nothing visible.

**When:** It bites when an unfamiliar dev reaches for Set/Map for
deduplication or as a cache, or for Date for "last updated" UX.
Symptoms: counter does not change, deduped list does not rerender,
"last updated 2 minutes ago" stays at 0 forever.

**How:** Always re-create-and-reassign for Date / Set / Map. Pattern A
in SKILL.md and Example 2 in references/examples.md show the shape.

## 2. `@track` plus `@api` on the same field is unsupported

**What:** Decorating a field with both `@api` and `@track` is accepted
by the compiler but produces undefined behavior — sometimes the parent
sees changes, sometimes not, depending on whether the parent re-passes
the prop.

**When:** It bites when a developer wants a public input that also
participates in deep observation. Symptom: parent assigns
`<c-child obj={parentObj}></c-child>`, child mutates `obj.x` in place,
parent does not see the change (or sometimes does, intermittently).

**How:** Never combine the two. Public props (`@api`) are read-only
contracts; if the child needs to "edit" the input, it should fire an
event with the new value and let the parent reassign.

## 3. Reactive proxies break `instanceof`

**What:** `this.someInstance instanceof MyClass` may return `false`
when `someInstance` is wrapped by the reactive proxy. The proxy is a
different object identity from the original.

**When:** It bites when an external library or your own code uses
`instanceof` to dispatch on type. Pattern matching on
`if (x instanceof Date)` after assigning a Date to a class field
returns false (and would not make the Date reactive anyway — see #1).

**How:** Avoid `instanceof` checks on reactive-tracked references. Tag
the type with a string discriminator (`x.__kind === 'date'`) or store
the value in a non-reactive `_dateBacking` field plus a reactive
serialized form (`isoString`).

## 4. `renderedCallback` fires more aggressively than Aura's `afterRender`

**What:** `renderedCallback` runs after EVERY render, including renders
caused by reactive property changes. Aura's `afterRender` ran once on
initial render unless explicitly re-fired.

**When:** It bites Aura migrations that initialized chart libraries,
sortable.js, or DOM-mutating code in `afterRender`. The LWC version
re-initializes on every prop change, leaving stacked listeners,
duplicate charts, or memory leaks.

**How:** Guard with `_hasRenderedOnce` for one-time setup. For
genuinely-on-every-render needs, ensure the work is idempotent (or use
a render-difference check before doing it again).

## 5. Spread-and-reassign is O(n); large arrays need a different shape

**What:** `this.items = [...this.items, newItem]` is the recommended
update pattern, but it allocates a fresh array of size n+1 every time.
For a 100k-item list with 60 ops/sec (e.g., live pricing feed),
spread-and-reassign is the bottleneck.

**When:** It bites when a component owns a large, frequently-mutating
collection. Symptoms: input lag during typing, jank during scroll,
profiler shows the spread as the hot path.

**How:** Three options. (1) Move the data behind an `@wire` adapter
that pages it. (2) Accept `@track` and `push`/`splice`. (3) Move state
to a shared module / Lightning Message Service so the component
re-renders only the slice it cares about.

## 6. `apiVersion` defaults can hide reactivity behavior changes

**What:** A component without an explicit `apiVersion` in
`js-meta.xml` inherits the org's default API version. After a release,
the org default may shift; a component that worked with `@track`-style
mutations may behave differently after a sandbox refresh because the
default API version moved.

**When:** It bites in long-lived orgs with components written across
many releases. The same `.js` source ships different runtime semantics
across components depending on each component's `apiVersion`.

**How:** Pin `apiVersion` explicitly in every `js-meta.xml`. Treat the
file as part of the contract, not a deploy-time accident.
