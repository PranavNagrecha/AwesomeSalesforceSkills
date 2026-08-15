---
name: flexcard-container-composition
description: "Design FlexCard composition: parent/child state flow, layout modes, actions, event wiring, and data source selection. Trigger keywords: flexcard, flex card composition, parent child flexcard, flexcard state, flexcard. NOT for the first-time FlexCard Hello-World, LWC alternatives, or Experience Cloud theming — use admin/flexcard-requirements."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Performance
  - Operational Excellence
triggers:
  - "flexcard composition design"
  - "parent child flexcard state"
  - "flexcard event wiring"
  - "flexcard datasource selection"
  - "flexcard action types"
  - "child flexcard not calling its data source"
tags:
  - omnistudio
  - flexcard
  - composition
  - ui
inputs:
  - UI mock or wireframe
  - Data sources available (IP, DataRaptor, REST, Apex)
  - Required actions (OmniScript launch, update record, fire event)
outputs:
  - FlexCard composition plan (parent / child / state map)
  - Datasource binding and action wiring decisions
  - Layout mode selection (card / list / table / none)
dependencies:
  - omnistudio/integration-procedure-cacheable-patterns
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
runtime_orphan: true
---

# FlexCard Container Composition

Use this skill when deciding how a FlexCard surface should be split — one card
or several, parent/child or siblings, which data source per card, how the
pieces talk — and when a correctly-configured child card is inexplicably not
calling its data source. Composition choices on this platform are performance
choices and, more often than teams expect, security choices.

---

## Data Source Selection

The Data Source wizard offers exactly ten types. Naming yours exactly is what
lets a reviewer check the decision.

| Type | Verbatim description | Use |
|---|---|---|
| **Integration Procedures** | "uses an Integration Procedure to return data from multiple internal and external sources" | **default** — one place to cache, centralise errors, and enforce access |
| **Omnistudio Data Mapper** | "uses a Data Mapper Extract interface to return data from a Salesforce object" | single-object read, no aggregation |
| **Apex Remote** | "uses an Apex Remote class and method to return data" | logic that needs code |
| **Apex REST** | "uses a REST endpoint of an Apex class to return data" | an existing Apex REST service |
| **SOQL Query** | "uses the Salesforce Object Query Language (SOQL) to search an org's Salesforce data" | prototyping only |
| **SOSL Search** | "uses the Salesforce Object Search Language (SOSL) to construct text-based search queries" | cross-object text search |
| **Streaming API** | "uses the Salesforce Streaming API to send notifications of general events" | server-pushed events |
| **SDK** | "uses a method from a Software Development Kit (SDK) to get data to populate fields" | SDK-backed integration |
| **Custom** | "uses sample JSON to set up a Flexcard with temporary data that'll eventually be replaced" | design-time scaffolding |
| **None** | for child FlexCards fed by their parent | any Data-Node-fed child |

**SOQL Query and Custom are prototyping data sources.** Neither has anywhere to
put field-level security, a Cache Block, `requiredPermission`, or an error
branch. Ship on Integration Procedures or Data Mapper with
`fieldLevelSecurityEnabled` true — and project down to the fields the card
actually renders, because the payload lands in the browser whether or not the
template shows it.

---

## Parent To Child: Two Mechanisms, And They Do Not Compose

The parent's Flexcard element has three properties that matter:

| Property | Purpose |
|---|---|
| **Flexcard Name** | which child card to embed |
| **Data Node** | pass "a record or an array of records to the child" — `{record}` for the current record, `{records}` to send all data |
| **Attributes** | pass specific values — attribute name and value, e.g. `Id` → `{Id}` |

Attributes arrive in the child's **Input Map**; the child references them as
`{Parent.Id}`.

**The override rule**, verbatim, and it is the single most useful fact in this
skill:

Selecting a parent Data Node **silently overrides** a child's own data source,
configured or not — the single most common cause of "my child card isn't
fetching". Quoted in [`references/gotchas.md`](references/gotchas.md).

Selecting a Data Node **silently disables the child's own data source**. So:

```text
child renders what the parent already has
    -> select Data Node, set child data source to None (for legibility)

child needs MORE or FRESHER data
    -> leave Data Node UNSELECTED, pass an Attribute, let the child fetch

need a parent-supplied record AND an independent fetch
    -> these are siblings, not parent/child. Use a pubsub channel.
```

A child that "isn't calling its Integration Procedure" is this rule roughly
every time. Check the parent's element before investigating the child.

---

## Sibling Communication: The Real pubsub API

```javascript
import pubsub from "lightning/omnistudioPubsub";
```

| Method | Signature |
|---|---|
| `register` | `register(eventName, callbackobj)` — registers handlers to a channel |
| `unregister` | `unregister(eventName, callbackobj)` — removes handlers from a channel |
| `fire` | `fire(eventName, action, payload)` — fires to all handlers on a channel |

Three things the signatures hide:

1. **The first argument is a channel.** The official example passes
   `"testchannel"`. Individual event names are **keys inside the callback
   object**, mapped to bound handlers. Passing an event name and a bare function
   — the shape every other pubsub library uses — subscribes to a channel nobody
   publishes to, silently.
2. **Retain the callback object.** Teardown requires "both the channel name and
   instance of your event handler objects"; an equivalent fresh object
   unregisters nothing.
3. **Names are a flat, page-wide namespace.** Prefix by workspace —
   `quoteworkspace`/`quoteselected` — not by component, and never ship
   `rowselected`.

---

## States Are UX, Not Authorization

"A Flexcard state determines what the user can see and do on the card," and
conditions select the matching state from data the browser already holds. The
evaluation is client-side.

So placing an action only in an `AtRisk` state hides it; it does not prevent
it. Authorization lives on the action's target — the OmniScript's or
Integration Procedure's `requiredPermission`, plus the running user's object,
field, and sharing permissions. The two look identical for a well-behaved user,
which is why the conflation survives review.

Past about three states, prefer separate cards plus a container: overlapping
state conditions are invisible to a reader holding seven layouts in mind.

---

## Publishing Targets Constrain The Design

FlexCards publish to Lightning pages via Lightning App Builder, Community and
portal pages via Experience Builder, external content management systems such
as Adobe Experience Manager, and custom web containers such as Heroku. Two
consequences: use the **Navigate** action type rather than composing a
`/lightning/r/...` path, and test as a user from the target audience in the
target host — the author's preview runs with the author's permissions.

---

## Recommended Workflow

1. Sketch the surface and mark the boundaries where the *data's audience or
   lifetime* changes. That, not the visual layout, is where the card boundary
   belongs.
2. For each card, pick exactly one data source by its exact type name. Default
   to Integration Procedures; use Data Mapper for a single-object read; never
   ship SOQL Query or Custom.
3. Decide parent/child versus siblings. Child fed by a **Data Node** when it
   renders what the parent has; **Attributes** plus its own fetch when it needs
   more; siblings on a pubsub channel when the pieces are genuinely
   independent. Remember Data Node and an independent child fetch do not
   compose.
4. Write the event contract before wiring: channel, event, payload shape,
   publisher, consumers, version. Prefix channels by workspace.
5. Separate immutables from mutables. Input parameters and Attributes carry
   immutables and are evaluated at render; channel events carry anything that
   must change during the card's life.
6. Define states and check their conditions do not overlap. Enforce anything
   security-relevant on the action's target, not on the state.
7. Preview in every required form factor, then verify in the target host as a
   user from the target audience — comparing the network payload, not only the
   rendered card.

---

## Review Checklist

- [ ] Each card has exactly one data source, named by its exact type
- [ ] No SOQL Query or Custom data source on a shipping card
- [ ] Data sources project down to the fields the template renders
- [ ] `fieldLevelSecurityEnabled` true on Data Mapper sources
- [ ] No child has both a selected parent Data Node and its own data source
- [ ] pubsub `register()` passes a **channel** plus a callback **object**
- [ ] Callback object retained on the component and reused at teardown
- [ ] Channels prefixed by workspace; no generic event names
- [ ] Event contract written down and versioned
- [ ] No state condition relied on for authorization
- [ ] State conditions do not overlap
- [ ] Navigation uses the Navigate action type, no hardcoded paths
- [ ] No DML against `OmniUiCard` anywhere
- [ ] Verified in the target host as a target-audience user, payload compared

---

## Worked Examples (see `references/examples.md`)

- *The ten data source types* — exact labels and when each fits
- *Account overview* — one card, one Integration Procedure, four sections
- *Parent to child* — Data Node vs Attributes, and the override rule
- *Sibling cards* — the real `lightning/omnistudioPubsub` API
- *Quotes list to quote detail* — why siblings beat parent/child here
- *The SOQL data source is a prototyping tool* — the IP equivalent
- *States are conditional layouts* — including what they do not secure

## Common Gotchas (see `references/gotchas.md`)

- A selected Data Node silently disables the child's data source
- `register()`'s first argument is a channel, not an event
- Teardown needs the same object instance, not an equivalent one
- Channel and event names share a flat, page-wide namespace
- Every data source on the page fires at render
- A state hides an action; it does not prevent it
- `OmniUiCard` is marked internal use only — never DML it

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- A generic pubsub API instead of `lightning/omnistudioPubsub`
- Passing an event name where a channel is expected
- Inventing a child-card data-passing mechanism (`JSON.stringify` bridges)
- Missing the Data Node override rule
- The SOQL data source on a user-facing card
- Treating a state as an access control
- The fat card
- Hardcoded URLs in navigation actions

---

## Related

- **omnistudio/flexcard-design-patterns** — layout, styling, and single-card
  design. This skill is the composition layer above it.
- **omnistudio/integration-procedure-cacheable-patterns** — how to make a hot
  card's data source fast without breaking its audience isolation.
- **omnistudio/omnistudio-custom-lwc-elements** — when a card needs behaviour no
  built-in action type covers.
- **omnistudio/omnistudio-security** — guest and Experience Cloud exposure,
  `requiredPermission`, and enforcing what a state only hides.

## Official Sources Used

See `references/well-architected.md` for the full source list with the specific
claim each source grounds.
