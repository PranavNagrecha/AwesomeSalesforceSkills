# LLM Anti-Patterns — Custom Notification Type Design

## Anti-Pattern 1: Notify On Every Event

**What the LLM generates:** record-triggered flow firing CNT on any
update.

**Why it happens:** "more signal is better."

**Correct pattern:** notify on actionable transitions only.

## Anti-Pattern 2: Multi-Channel Everything

**What the LLM generates:** bell + desktop + mobile + Slack for all
CNTs.

**Why it happens:** feature parity impulse.

**Correct pattern:** match urgency to channel; most CNTs are bell-only.

## Anti-Pattern 3: List-View Deep Links

**What the LLM generates:** deep link to a filtered list view.

**Why it happens:** admin thinks of their own workflow.

**Correct pattern:** link to the specific record needing action.

## Anti-Pattern 4: No Throttling

**What the LLM generates:** a CNT that fires on every status change,
fires 5 times during a rapid edit session.

**Why it happens:** "each change matters."

**Correct pattern:** coalesce with a last-notified-at field; set minimum
interval.

## Anti-Pattern 5: Skip The Registry

**What the LLM generates:** each feature ships its own CNT with no
central list.

**Why it happens:** per-feature delivery.

**Correct pattern:** register every CNT with owner + measurable outcome;
quarterly pruning.

## Anti-Pattern 6: Classic URL In Deep Link

**What the LLM generates:** `/<id>` style URL.

**Why it happens:** pre-Lightning habit.

**Correct pattern:** `/lightning/r/<Object>/<Id>/view`.
