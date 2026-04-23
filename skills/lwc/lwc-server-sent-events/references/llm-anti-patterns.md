# LLM Anti-Patterns — LWC Streaming

## Anti-Pattern 1: No `disconnectedCallback`

**What the LLM generates:** subscribes in `connectedCallback`, nothing in
`disconnectedCallback`.

**Why it happens:** happy-path symmetry missed.

**Correct pattern:** always unsubscribe.

## Anti-Pattern 2: Per-Row Subscription

**What the LLM generates:** list iterates rows; each row subscribes.

**Why it happens:** copy-paste lifecycle.

**Correct pattern:** subscribe once, dispatch locally.

## Anti-Pattern 3: Trust `-1` For Reliability

**What the LLM generates:** "just use replay -1."

**Why it happens:** documentation default.

**Correct pattern:** reliability-sensitive UIs track replayId or accept
eventual re-sync from a secondary API.

## Anti-Pattern 4: Event Handler Not Idempotent

**What the LLM generates:** "increment a counter when event arrives."

**Why it happens:** treats push as single-delivery.

**Correct pattern:** assume duplicate / out-of-order; handlers must tolerate.

## Anti-Pattern 5: Subscribing In `renderedCallback`

**What the LLM generates:** subscribe inside `renderedCallback`.

**Why it happens:** confusion about lifecycle.

**Correct pattern:** one-time setup belongs in `connectedCallback`.
