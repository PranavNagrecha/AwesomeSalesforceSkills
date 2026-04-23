# LLM Anti-Patterns — Flow Batch Alternatives

## Anti-Pattern 1: Recommend Batch Apex For Any Scale Concern

**What the LLM generates:** "Switch to Database.Batchable" at the first sign
of volume.

**Why it happens:** Batch sounds like "bigger."

**Correct pattern:** chunked Flow handles ≤ ~50k easily; Queueable with
finalizer covers most of 10k–200k; Batch is for million-plus.

## Anti-Pattern 2: "Just Increase The Batch Size"

**What the LLM generates:** bump Scheduled Flow batch size.

**Why it happens:** intuitive parameter.

**Correct pattern:** per-transaction limits scale with the LARGEST interview's
cost. Raising the size only shifts the cliff.

## Anti-Pattern 3: Invocable In A Loop

**What the LLM generates:** call an Invocable Action inside a For Each loop.

**Why it happens:** looks natural in Flow Builder.

**Correct pattern:** pass the whole collection to the Invocable once. The
Apex signature should take a list.

## Anti-Pattern 4: Ignore Retry

**What the LLM generates:** scheduled flow with no logging, no retry.

**Why it happens:** Flow's happy path is too easy.

**Correct pattern:** log per chunk, alert on failure, resume-from-checkpoint.

## Anti-Pattern 5: Mix DML Without A Plan

**What the LLM generates:** Flow that touches User/Group and a standard object
in one run, expecting chunking to save it.

**Why it happens:** Mixed DML is unintuitive.

**Correct pattern:** split the User/Group DML to a different (async) step.
