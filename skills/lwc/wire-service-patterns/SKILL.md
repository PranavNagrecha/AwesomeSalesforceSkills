---
name: wire-service-patterns
description: "Use when designing or reviewing Lightning Web Components that use `@wire`, Lightning Data Service, UI API, or the GraphQL wire adapter, especially for reactive parameters, cache behavior, and refresh strategy. Triggers: 'wire service', 'refreshApex', 'reactive parameter', 'getRecord', 'wire vs imperative Apex', 'cacheable=true', 'notifyRecordUpdateAvailable', 'wired data is read-only', 'getPicklistValues recordTypeId'. NOT for forcing a refresh after DML — use lwc/lwc-wire-refresh-patterns. NOT for imperative Apex on a click — use lwc/lwc-imperative-apex."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - User Experience
tags:
  - wire-service
  - lightning-data-service
  - refreshapex
  - reactive-parameters
  - graphql-wire
  - cacheable-apex
triggers:
  - "when should i use wire vs imperative apex"
  - "refreshapex not updating my component"
  - "reactive wire parameter not firing"
  - "getrecord wire returns undefined"
  - "graphql wire uses errors instead of error"
  - "LWC not updating when data changes"
  - "component not updating when record changes"
  - "debug wire data arriving after renderedCallback"
  - "explain wire service and lifecycle hook order"
  - "annotate an apex method cacheable true so it can be wired"
  - "refresh wired data after an imperative apex save"
  - "call notifyRecordUpdateAvailable after imperative dml"
  - "handle data and error separately in a wired function"
  - "fix invalid mutation cannot set is read-only on wired data"
  - "wire getrecord with a reactive recordid on a record page"
  - "chain getobjectinfo into getpicklistvalues with a reactive record type id"
  - "test a wire adapter in jest with emit"
  - "decide between fields and layoutTypes on getRecord"
  - "wire vs imperative apex in lwc and getRecord wire fields"
inputs:
  - "data source such as UI API, Apex, or GraphQL"
  - "whether the component only reads data or also mutates it"
  - "what should trigger refresh or re-evaluation"
outputs:
  - "wire-service pattern recommendation"
  - "review findings for cache, reactive parameters, and refresh behavior"
  - "decision on wire adapters, LDS forms, or imperative Apex"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when the LWC data path needs to be intentional rather than incidental. The wire service is excellent for declarative, cache-aware reads, but only if the component understands immutability, reactive parameters, and when wire adapters will or will not re-evaluate. Use it when the LWC is not updating when data changes—often because the wire adapter isn't re-evaluating or a refresh wasn't triggered.

## Before Starting

- Is the component only reading Salesforce data, or does it also perform writes that should happen imperatively?
- Is the best data source a base component, a UI API wire adapter, an Apex wire adapter, or the GraphQL wire adapter?
- What event should actually refresh the data: parameter change, record change notification, or an explicit refresh call?

## Questions to Ask Before Configuring

Ask these before the first `@wire` is written. Every row traces to a documented platform
behaviour in `references/gotchas.md` that punishes the default assumption.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which object is this, and does User Interface API support it?" | LDS covers all custom objects and the standard objects UI API supports; custom metadata types are not supported, and Task and Event are the named escapes to Apex | The adapter choice settled before any code — a UI API wire, or a cacheable Apex wire, not a workaround on the wrong one |
| "Is every value in the config defined at first render, and what does 'not yet chosen' mean — `null` or `undefined`?" | An `undefined` config property means no provisioning *and* no error; for a wired Apex method a `null` param still calls the method while `undefined` does not | A deliberate sentinel, plus an Apex method written to survive the one that fires |
| "Does the component need to look at `data` and `error`, or just hand them to the template?" | The property form is right only when the template consumes `{data, error}` as-is; the function form is required to retain the provisioned object for `refreshApex()` | The form chosen for a reason, and the `wiredXResult` field that makes refresh legal later |
| "Which fields, exactly — or is an admin meant to control them?" | `fields` and `layoutTypes` are alternatives; a layout means the component must handle every field the layout carries for the context user, and polymorphic fields error out of `fields` entirely | A field list that is either explicit or explicitly delegated, with `optionalFields` covering anything the user may not see |
| "After this component writes, what else on the page is showing the same record?" | `refreshApex()` refreshes the Apex wire's own cache; only `notifyRecordUpdateAvailable()` reaches every LDS wire on that record, and using `refreshApex` on a non-Apex adapter is deprecated | One refresh call per cache, chosen by adapter — not one call and a hope |
| "Will anything sort, filter, annotate, or edit the provisioned rows?" | `@wire` output sits behind a read-only proxy; an in-place edit throws `Invalid mutation … is read-only`, and a shallow copy leaves nested objects still frozen | A copy boundary drawn once, at the wire handler, instead of a runtime error found in production |
| "How will the loading, empty and error states each be proved in a test?" | Before the first emission both `data` and `error` are `undefined` and the wire is *not* in an error state, so "no data" and "failed" are different states that look identical in careless code | Three Jest cases driven by `emit()` on the imported adapter, so the states cannot collapse into one |

What a proper wire design adds over just making it work: the config's completeness, the
copy boundary and the post-write refresh become three written decisions with a checker rule
and a Jest assertion behind each, so a later edit that breaks one fails a test instead of
producing stale UI nobody can reproduce.

---

## Core Concepts

### Wire Is A Provisioning Model, Not A Lifecycle Hook

Wire adapters provision data when their configuration is complete and when Salesforce determines fresh data should be emitted. The component should not assume wire execution timing matches `connectedCallback()` or `renderedCallback()`. The framework owns when data arrives.

Knowing the concrete init sequence is what lets you debug the classic "flash of undefined data" bug. For a Lightning Data Service wire the order is:

1. `constructor()` runs.
2. LDS provisions an empty placeholder — an object where both `data` and `error` are `undefined`. This happens *before* your first render, so the wired property is defined-but-empty, not missing.
3. `connectedCallback()`, `render()`, and `renderedCallback()` fire in that order. On this first pass the real data has **not** arrived yet — `data` is still `undefined`.
4. Data becomes available from the adapter asynchronously and is set on the `data` property (with `error` remaining `undefined`).
5. If the template consumes that data, `render()` and `renderedCallback()` fire **again**.

Guarding the template on `data` being truthy — or handling `undefined` in `renderedCallback()` — is what prevents the empty first pass from rendering as broken UI. A wired *function* is looser still: it "is invoked whenever a value is available, which can be before or after the component is connected or rendered."

### Wire Emissions Are Multiple, Asynchronous, And Unordered

A wire is a stream, not a single resolved value. An LDS wire can emit data multiple times without the component changing its configuration; LDS controls those emits and they aren't tied to the LWC lifecycle. That is why `renderedCallback()` can fire repeatedly for reasons the component never initiated — a cache update elsewhere in the app can push a fresh value.

Wire adapter calls are also asynchronous unless the data is already cached, so the order of response and promise resolution is not sequential. Do not write logic that assumes wire A resolves before wire B, or that a wired value is present just because an imperative promise resolved. Each emission is a newer, immutable version of the previous value — treat the property as a read-only stream you react to, never a variable you populate at a known moment.

### Reactive Parameters Must Become Real Values

Dynamic wire parameters prefixed with `$` only work when the underlying values are defined. If a required reactive parameter is `undefined`, the wire adapter is not evaluated. This is one of the most common reasons a wire "doesn't fire."

Three things narrow that rule and are worth holding separately:

- **`$` is top-level only.** Nesting it inside an array or object literal makes it a literal string, not a reference. Build the whole collection as one reactive property instead.
- **`null` is not `undefined`.** For a wired Apex method, a `null` parameter calls the method; only `undefined` suppresses the call. The Apex method therefore has to tolerate `null`.
- **Reactive means re-provisioned.** When the value changes, new data is provisioned and the render cycle runs again — so never assign a reactive config property from inside `renderedCallback()`.

Private properties, getter-setter pairs, and `@api` properties can all be reactive config values.

### Property Form Versus Function Form

| | Property form | Function form |
|---|---|---|
| Shape | `@wire(adapter, cfg) foo;` → `foo.data` / `foo.error` | `@wire(adapter, cfg) handler({data, error}) {}` |
| Use when | The template consumes `{data, error}` as-is | The component must branch, transform, or copy |
| First value | Assigned after construction, before any other lifecycle event, as `{data: undefined, error: undefined}` | Not invoked until a value is available |
| `refreshApex()` | Pass the property itself | Pass the whole provisioned argument — retain it in a field *before* destructuring |
| Destructuring order | n/a | Irrelevant; `{data, error}` and `{error, data}` are equivalent because it is an object |

The `data` and `error` property names are hardcoded in the API for both forms. The GraphQL wire adapter is the one exception: it uses `errors`, for compatibility with the GraphQL response specification.

### `cacheable=true` Is The Contract That Makes `@wire(apexMethod)` Legal

An Apex method can only be wired if it is annotated `@AuraEnabled(cacheable=true)`, and it can only be marked cacheable if it does not mutate data. That single annotation is what splits an LWC's Apex surface in two: cacheable reads may be wired *or* called imperatively, and everything that writes must be imperative. Apex limits apply per invocation, so two wired methods are two separate limit contexts, not one.

### Two Data Sources Means Two Caches

LDS manages its own data; Apex data is unmanaged and must be refreshed by the component. That produces a three-way routing rule after any write:

| The stale read is… | Refresh with | Note |
|---|---|---|
| An Apex `@wire` | `refreshApex(provisionedResult)` | Re-runs with the config bound to the wire; the resolved Promise value is meaningless |
| A UI API wire (`getRecord`, `getRecords`, related lists) | `notifyRecordUpdateAvailable([{ recordId }])` | Reaches every wire on those records in every instantiated component; `refreshApex` here is deprecated |
| A GraphQL wire | `refreshGraphQL(result)` / `refresh()` | v2 is `lightning/graphql`; v1 `lightning/uiGraphQLApi` is superseded |

Refresh once, after the mutating operation completes. Never poll with `setTimeout()` or `setInterval()` — if you cannot tell when a mutation finishes, give the user a refresh button instead. Apex and LDS do not share a cache at all, so a component that reads the same data through both can show two different answers.

### Wired Data Should Be Treated As Immutable Input

The wire service gives the component data to render, not mutable state to edit in place. Provisioned objects are wrapped in a read-only proxy; assigning into them raises `Invalid mutation … is read-only`. Make a shallow copy before transforming — and remember that shallow copies do not copy nested objects, so a spread of a UI API record leaves the `fields` object still frozen.

### Wire And Imperative Calls Solve Different Problems

Use wire for cache-aware reads and declarative reactivity. Use imperative Apex or LDS mutation APIs for creates, updates, deletes, and explicit user-triggered actions. Imperative is also the only option for objects UI API does not support, for loading records by criteria, for transactional multi-record work, and for anything that must run at a moment you choose.

## Common Patterns

### UI API Wire For Record Reads

**When to use:** The component reads record data and should inherit Lightning Data Service caching, sharing, CRUD, and FLS behavior.

**How it works:** Use adapters such as `getRecord` or object-info wires with schema imports and reactive record identifiers. Prefer `fields` over `layoutTypes`; use `optionalFields` for anything the running user may not be able to see, since a missing field in `fields` is an error while a missing `optionalField` is simply absent.

**Why not the alternative:** Custom Apex for standard record reads adds avoidable maintenance and can bypass built-in data protections.

### Wire Chained Into Wire

**When to use:** One adapter's output is another's required input — the canonical case being `getObjectInfo` → `defaultRecordTypeId` → `getPicklistValues`.

**How it works:** Assign the intermediate value to a reactive property in the first wire's handler and reference it as `$prop` in the second. The second wire simply does not fire until the first lands, which is the gate working, not a bug.

**Why not the alternative:** Hardcoding a record type Id works until someone adds a record type. The master record type is `012000000000000AAA` only when there is no default.

### Imperative Mutation Plus Controlled Refresh

**When to use:** A user action updates data and the component must then refresh its wired state.

**How it works:** Perform the write imperatively, then refresh each stale cache with its own function per the routing table above. A component with both an Apex wire and a UI API wire over the same record needs both calls.

**Why not the alternative:** Expecting the wire adapter to notice every asynchronous server-side change leads to stale UI — an Apex trigger or auto-launched flow that changes the record does not re-evaluate the wire at all.

### GraphQL Wire For Multi-Entity Read Models

**When to use:** The component needs a richer read model than individual UI API wires can express cleanly, or it needs filtering, ordering, pagination, or dynamic record Ids.

**How it works:** Use the GraphQL wire adapter, remember that the response exposes `errors` instead of `error`, and keep the component read-focused. `lwc/lwc-graphql-wire` owns the query shape and pagination.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard record read with strong platform security defaults | UI API wire adapter or LDS base component | Built-in cache plus sharing, CRUD, and FLS |
| Object UI API does not support (Task, Event, custom metadata type) | Cacheable Apex wire | LDS supports custom objects and the standard objects UI API supports; not these |
| Records selected by criteria ("first 200 Accounts over $1M") | Apex or GraphQL | UI API does not express criteria-based loading |
| User clicks Save or Submit and writes data | Imperative call | Writes cannot be `cacheable=true`, so they cannot be wired |
| Complex read model across related entities | GraphQL wire adapter | Cleaner multi-entity read shape, plus filtering and pagination |
| Wire depends on a value not available at first render | Use reactive parameters and guard for `undefined` | The wire only evaluates when config is complete |
| Multiple records must change in one transaction | Apex | Each LDS function call is an independent transaction |

## Recommended Workflow

1. **Settle the adapter before the code.** Answer the seven questions above, checking the
   object against UI API support and the write path against `cacheable=true`. Record the
   answers in `templates/wire-service-patterns-template.md`; the Data Path table is the
   contract the rest of the steps implement.
2. **Choose property form or function form deliberately**, using the table in Core Concepts.
   If the component will ever call `refreshApex()`, it needs the function form and a
   `wiredXResult` field assigned *before* destructuring.
3. **Build from `references/code-examples.md`.** It carries the deployable slice: the
   `cacheable=true` controller plus its test, the bundle with `getRecord` on `$recordId`,
   the `getObjectInfo` → `getPicklistValues` chain, the function-form Apex wire, the
   spread-copy boundary, the `js-meta.xml`, `package.xml`, and the deploy order. Reuse
   `templates/lwc/patterns/wireServicePattern.js` for the minimal property-form read and
   `templates/lwc/component-skeleton/` for the loading and error shell.
4. **Model loading, empty and error as three states, not two.** Before the first emission
   both `data` and `error` are `undefined`; that is not an error. Branch on the provisioned
   result's presence, and normalise `error.body` for the array-versus-object split — or
   import the shared `errorUtils` module from `lwc/lwc-error-boundaries`.
5. **Write the refresh path at the same time as the write path.** One call per stale cache,
   chosen from the routing table. No `setTimeout` / `setInterval` polling.
6. **Pin the behaviour with the six Jest cases in `references/code-examples.md` § 5** —
   loading before any emit, a `getRecord.emit()` render, a copy-not-mutate assertion, empty
   versus loading, an Apex-shaped error, and a post-save assertion that `refreshApex` got
   the provisioned object and `notifyRecordUpdateAvailable` got `[{ recordId }]`.
   `lwc/lwc-testing` owns the harness and `jest.config.js`.
7. **Run the checker over the source tree:**
   `python3 scripts/check_wire_service_patterns.py --manifest-dir force-app --strict`.
   It flags a wired Apex method that is not `cacheable=true` (ERROR), in-place mutation of a
   wired result (ERROR), `refreshApex()` on something no wire provisioned, a `$` nested
   inside a collection, a wired function that reads `data` but never `error`, an imperative
   write with no refresh call, a reactive config property assigned in `renderedCallback()`,
   and a string literal passed where a matching `@api` property exists.

---

## Review Checklist

- [ ] The component uses wire only for read/provisioning use cases.
- [ ] Every wired Apex method is `@AuraEnabled(cacheable=true)` and does not mutate.
- [ ] Reactive parameters are defined intentionally and not left `undefined` accidentally.
- [ ] Every `$` reference is a top-level config value, never nested in an array or object.
- [ ] Wired results are cloned before UI-specific mutation or sorting.
- [ ] Loading, empty, and error are three distinct rendered states.
- [ ] `error.body` handling branches on array versus object.
- [ ] Refresh after writes uses one function per cache and never polls.
- [ ] Schema imports are used where referential integrity matters.
- [ ] GraphQL wire consumers handle `errors` rather than assuming `error`.

## Salesforce-Specific Gotchas

1. **A wire adapter does not guarantee when data arrives** — it can emit multiple times and is not tied to component lifecycle timing.
2. **Undefined reactive parameters stop evaluation** — many "wire isn't running" bugs are really incomplete configuration.
3. **`null` and `undefined` behave differently for wired Apex params** — `null` calls the method, `undefined` does not.
4. **A nested `$` is a literal string** — `['$ids']` is passed verbatim, not resolved.
5. **GraphQL wire returns `errors`, not `error`** — assuming the standard wire error shape causes broken error handling.
6. **Async changes outside the adapter do not auto-refresh** — Apex-triggered or Flow-triggered server updates need an explicit refresh strategy.
7. **`refreshApex()` on a non-Apex wire adapter is deprecated** — use `notifyRecordUpdateAvailable()` for UI API reads.
8. **`renderedCallback()` runs against undefined data on the first pass** — LDS provisions an empty `{data: undefined, error: undefined}` placeholder before the real value arrives.

Full write-ups with grounding: `references/gotchas.md`.

## Output Artifacts

| Artifact | Description |
|---|---|
| Data-path recommendation | Decision on UI API, Apex wire, GraphQL wire, or imperative pattern |
| Wire-service review | Findings on reactive params, immutability, refresh, and cache usage |
| Component bundle | `js` / `html` / `js-meta.xml` plus Jest suite, from `references/code-examples.md` |
| Refactor guidance | Concrete steps to fix stale data or misused wire patterns |

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are about to write the bundle: cacheable Apex controller + test, the wired component, `getObjectInfo` → `getPicklistValues` chain, `refreshApex` + `notifyRecordUpdateAvailable`, `js-meta.xml`, `package.xml`, Jest suite, deploy order, verification table |
| `references/gotchas.md` | A wire does not fire, fires with a literal string, refuses a mutation, refreshes nothing, or returns HTTP 200 with a failed subrequest |
| `references/llm-anti-patterns.md` | Reviewing generated LWC code — the eight shapes assistants produce most often, each with a detection hint |
| `references/examples.md` | You want the shorter narrative walk-throughs before committing to an adapter |
| `references/well-architected.md` | Justifying the choice in a design review, or you need the official source behind a specific claim |
| `templates/wire-service-patterns-template.md` | Step 1 of the workflow — the worksheet that becomes the data-path contract |

## Related Skills

- `lwc/lwc-imperative-apex` — use when the call is click-driven or non-cacheable; that skill owns the imperative side of the same Apex class.
- `lwc/lwc-wire-refresh-patterns` — use for RefreshView API and cross-component refresh; this skill covers refreshing after the component's own write.
- `lwc/lwc-lds-writes` — use when the write itself is `createRecord` / `updateRecord` / `deleteRecord` or a record form.
- `lwc/lwc-graphql-wire` — use when the read model is a GraphQL query, including pagination and `errors` handling.
- `lwc/lwc-error-boundaries` — use for the shared `errorUtils` normaliser and `errorCallback`; that skill owns error normalisation.
- `lwc/lwc-testing` — use for the Jest harness, `jest.config.js`, and mocking conventions.
- `lwc/lwc-reactive-state-patterns` — use when the question is component-local reactivity rather than server provisioning.
- `lwc/lifecycle-hooks` — use when render timing or cleanup is the real problem rather than provisioning strategy.
- `apex/soql-security` — use when the component relies on custom Apex reads that need secure data access review.
- `lwc/lwc-offline-and-mobile` — use when the wire strategy must also account for mobile or offline behavior.
