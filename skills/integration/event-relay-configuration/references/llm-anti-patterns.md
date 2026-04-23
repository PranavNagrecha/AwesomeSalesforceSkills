# LLM Anti-Patterns — Event Relay

## Anti-Pattern 1: Standard PE For Relay

**What the LLM generates:** use a standard Platform Event for relay.

**Why it happens:** "Platform Event = Platform Event."

**Correct pattern:** High-Volume Platform Event for relay use cases;
standard PE is not sized for this.

## Anti-Pattern 2: No Watermark

**What the LLM generates:** "set replay to LATEST."

**Why it happens:** simplest default.

**Correct pattern:** store replayId downstream; resume from the watermark
after an outage.

## Anti-Pattern 3: Non-Idempotent Consumer

**What the LLM generates:** Lambda that writes on every event.

**Why it happens:** "exactly-once illusion."

**Correct pattern:** idempotency key = (recordId, commitTimestamp) or
similar.

## Anti-Pattern 4: No External ID On IAM Role

**What the LLM generates:** trust policy with Salesforce account principal
only.

**Why it happens:** minimal config.

**Correct pattern:** include an external id; rotate it per relay.

## Anti-Pattern 5: Assume Cross-Region Works

**What the LLM generates:** one connection fanning to us-east-1 and
eu-west-1.

**Why it happens:** EventBridge supports cross-region rules — but relay
targets one bus.

**Correct pattern:** one relay per region; or a single bus with
downstream rules fanning.
