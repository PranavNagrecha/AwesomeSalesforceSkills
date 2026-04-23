# LLM Anti-Patterns — Flow Transaction Finalizer

## Anti-Pattern 1: Pre-Save Email

**What the LLM generates:** add a Send Email action in a before-save
record-triggered flow.

**Why it happens:** Flow Builder offers it; it "works" in demos.

**Correct pattern:** emails belong post-commit. Use scheduled path or
platform event.

## Anti-Pattern 2: Assume After-Save Is Post-Commit

**What the LLM generates:** "after-save flow runs after commit, so callouts
are safe."

**Why it happens:** name suggests temporal ordering.

**Correct pattern:** after-save runs AFTER the save step but BEFORE commit
in the outer transaction. Rollback still drops the work.

## Anti-Pattern 3: Catch And Continue

**What the LLM generates:** Flow fault path that swallows the exception
and moves on.

**Why it happens:** removes visible errors.

**Correct pattern:** log every failure; alert; do not mask.

## Anti-Pattern 4: Flow Retries Via Scheduled Flow Loop

**What the LLM generates:** "if the callout fails, schedule it for the
next run."

**Why it happens:** no native retry in Flow.

**Correct pattern:** Queueable + Finalizer owns retry semantics; Flow
should escalate, not reinvent.

## Anti-Pattern 5: Finalizer Without State

**What the LLM generates:** finalizer that logs "done" with no job id or
outcome.

**Why it happens:** copy-paste.

**Correct pattern:** finalizer logs job id, outcome, retry count. Makes
the pipeline debuggable.
