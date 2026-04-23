# LLM Anti-Patterns — FlexCard State Management

## Anti-Pattern 1: Recommending `Reload Card` For Every Action

**What the LLM generates:** Every action chain ends with `Reload Card` "to be safe."

**Why it happens:** Reload appears to always work. But it triggers a full re-init, re-runs every data source, and resets user scroll/expansion. On a busy page it produces visible flicker and redundant governor use.

**Correct pattern:** Choose the narrowest refresh target — element → card state → card data → reload — that produces the correct result.

## Anti-Pattern 2: Using Session Variables As Shared State Between Cards

**What the LLM generates:** Card A writes `selectedRecordId` to a session variable; Card B polls it.

**Why it happens:** Session variables are easy to reach. But they are page-scoped globals — two cards can silently collide, and there is no subscription signal to drive the read.

**Correct pattern:** Use input parameters for parent-child and pubsub events for sibling coupling. Reserve session variables for short-lived handoffs with namespaced names.

## Anti-Pattern 3: Binding Conditional Visibility To Unmapped Fields

**What the LLM generates:** `{Account.Is_Priority__c}` in a visibility rule even though the field is not in the data source projection.

**Why it happens:** The field exists on the record, so it feels available. But conditional visibility reads from the cached response. Missing fields evaluate as false forever.

**Correct pattern:** Include the field in the data source projection OR have the action's output mapping write the value into the cache.

## Anti-Pattern 4: Refreshing State When Data Changed

**What the LLM generates:** `Refresh Card State` after `Record/Update`.

**Why it happens:** State refresh feels lighter than data refresh. But state refresh reads cache; the mutated record is not visible until the data source re-runs.

**Correct pattern:** Use `Refresh Card Data` after any server-side mutation. Use `Refresh Card State` only when the derived/computed values in cache changed.

## Anti-Pattern 5: Generic Pubsub Event Names

**What the LLM generates:** `pubsub.publish("refresh")`.

**Why it happens:** One-word names look tidy. But they collide across the page, and every subscribing card refreshes on every publisher's event.

**Correct pattern:** Namespace pubsub events: `accountSummary.caseCreated`, `opportunity.stageChanged`. Document the publisher and payload contract next to the card definition.
