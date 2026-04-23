---
name: flexcard-state-management
description: "Use when designing FlexCard actions, conditional visibility, and state that must survive navigation, refresh, or parent/child card transitions. Triggers: 'flexcard state', 'flexcard conditional visibility', 'flexcard actions', 'flexcard refresh', 'child flexcard state'. NOT for raw LWC state or for OmniScript step state."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
  - Performance
triggers:
  - "flexcard state disappears when user navigates"
  - "conditional visibility on flexcard not re-evaluating"
  - "how should parent and child flexcard share state"
  - "flexcard action needs to refresh a sibling card"
  - "flexcard data session cache vs pubsub"
tags:
  - omnistudio
  - flexcard
  - state-management
  - conditional-visibility
  - pubsub
inputs:
  - "flexcard layout and parent/child relationships"
  - "actions bound to elements and their refresh targets"
  - "conditional visibility rules and the fields they depend on"
outputs:
  - "state flow diagram across parent, child, and sibling cards"
  - "refresh strategy (element, card, data source) per action"
  - "conditional visibility and pubsub recommendations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# FlexCard State Management

FlexCard state problems rarely look like state problems at first. They look like "the card didn't refresh," "the button did nothing," or "the child card shows stale data." The underlying cause is almost always that FlexCard state has multiple layers — data source state, element-level state, conditional visibility state, and pubsub state — and the author treated them as a single thing. Good FlexCard design names each layer explicitly and decides, per action, which layer must refresh and which must not.

FlexCard holds data in a local session cache keyed by the data source. Actions operate on that cache — they can refresh an element, refresh the whole card, or re-invoke the data source. Conditional visibility reads from the cache, not from Salesforce. That means a record update from elsewhere does not propagate until an action or pubsub tells the card to refresh.

Parent and child FlexCards share state only by contract: parent passes parameters down, child refreshes upward via events or pubsub. A child FlexCard cannot reach into the parent's cache. A parent cannot force a child to refresh except via a pubsub event the child has subscribed to.

---

## Before Starting

- List each FlexCard involved and their parent/child relationships.
- Identify actions bound to buttons, icons, or menu items, and their targets.
- Identify conditional visibility rules and the fields or session variables they read.
- Note whether any card is embedded inside an OmniScript or a Lightning page — both change refresh semantics.

## Core Concepts

### State Layers

1. **Data source state** — the response cached after the data source ran. Survives until the card reloads or a `Refresh Card Data` action fires.
2. **Element state** — per-element bindings (e.g. a node's visibility flag). Re-evaluated on element refresh.
3. **Conditional visibility state** — a derived read of the data source state. It does not poll.
4. **Pubsub state** — ephemeral, runtime-only. Lost on navigation.
5. **Session variables** — name-scoped variables within the runtime; useful for short-lived coordination between cards.

### Action Refresh Targets

- `Refresh Card Data` — re-runs the data source; use when data could have changed server-side.
- `Refresh Card State` — re-renders from cache; use when only derived state changed.
- `Refresh Element` — re-renders one node; use when one button/row needs to update.
- `Refresh Parent` / `Refresh Sibling` — cross-card; requires pubsub or `omnistudioFlexCard` framework events.

### Cross-Card Coordination

Parent-child coordination uses input parameters and events. Sibling-to-sibling coordination uses pubsub. Do not try to reach into another card's cache — that coupling breaks when either card is redesigned.

---

## Common Patterns

### Pattern 1: Optimistic UI With Post-Save Refresh

Run the action, immediately update element state to reflect the expected outcome, then trigger `Refresh Card Data` on success to reconcile with the server.

### Pattern 2: Pubsub For Sibling Refresh

When card A's action should refresh card B, publish a named event from A and subscribe in B. Both cards still own their own data source; neither depends on the other's internal cache shape.

### Pattern 3: Parameter-Driven Child Rerender

Pass the controlling record ID as an input parameter to the child card. When the parent's selection changes, update the input binding — the child refreshes automatically because its parameters changed.

### Pattern 4: Session-Variable Handoff

When a parent action should hand a value to a sibling or to a nested OmniScript step, write to a session variable. Read it in the consumer. Treat these like global scope — name them carefully.

### Pattern 5: Conditional Visibility Gated On Action Completion

For "show after save" UX, bind visibility to a derived field that the action writes into the cache on success. Avoid binding visibility to raw `isLoading`-style flags; they fight with normal data source refreshes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Card shows stale value after record update | `Refresh Card Data`, not `Refresh Card State` | State refresh reads cache; data refresh re-queries |
| Child card needs to update when parent selection changes | Parameter-driven rerender | Cleanest coupling contract |
| Sibling card must refresh after a save | Pubsub event | No shared parent-owned state needed |
| Button should disable during action | Element-level state + action completion event | Avoid full-card refresh churn |
| Visibility depends on derived/computed state | Compute in data source or action, store in cache | Conditional visibility is not a function engine |

## Well-Architected Pillar Mapping

- **User Experience** — predictable refresh feels faster than aggressive full refresh; explicit targets avoid flicker.
- **Reliability** — explicit coupling contracts prevent cross-card bugs when one card is rewritten.
- **Performance** — element-level refresh avoids unnecessary data source calls.

## Review Checklist

- [ ] Each action names its refresh target deliberately.
- [ ] Parent/child coupling uses input parameters, not reach-in reads.
- [ ] Sibling coupling uses pubsub, not shared globals.
- [ ] Conditional visibility reads fields that exist in the cache after the governing action completes.
- [ ] Session variables are namespaced and documented.
- [ ] Refresh Card Data is used only when the server state could have changed.

## Recommended Workflow

1. Inventory — list the cards, their data sources, and the actions on each.
2. Classify refresh intent — element, card state, card data, or cross-card for every action.
3. Choose coupling — parameters for parent-child, pubsub for sibling.
4. Implement and simulate — test with the FlexCard preview's action trace.
5. Validate — run this skill's checker against the card metadata.
6. Document — record the state flow diagram alongside the FlexCard definition.

---

## Salesforce-Specific Gotchas

1. `Refresh Card State` does not re-run the data source; stale data persists.
2. Pubsub events do not survive navigation between Lightning pages.
3. Session variables are shared across the page, not just the card — collisions are common.
4. Conditional visibility uses the cached response, not live field values.
5. Child FlexCards inside an OmniScript step reset when the user navigates between steps.

## Proactive Triggers

Surface these WITHOUT being asked:

- Action uses `Refresh Card State` after a `Record/Update` → Flag High. Likely wanted `Refresh Card Data`.
- Child card reads parent's session variable without subscribing → Flag Medium. Fragile coupling.
- Pubsub event published with generic name (e.g. `refresh`) → Flag Medium. Namespace collision risk.
- Conditional visibility bound to a field the action does not write → Flag High. Will never toggle.
- Card uses `Reload Card` on every action → Flag Medium. Performance regression.

## Output Artifacts

| Artifact | Description |
|---|---|
| State flow diagram | Parent/child/sibling map with refresh arrows |
| Action refresh matrix | Per-action target and justification |
| Pubsub event catalog | Event names, publishers, subscribers |

## Related Skills

- `omnistudio/flexcard-design-patterns` — layout and composition.
- `omnistudio/omnistudio-cache-strategies` — data source caching.
- `omnistudio/omnistudio-lwc-integration` — when LWC embeds FlexCard.
- `omnistudio/omnistudio-debugging` — tracing action and refresh flow.
