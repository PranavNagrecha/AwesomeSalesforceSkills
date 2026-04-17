# Examples — OmniStudio Asynchronous Data Operations

## Example 1: Async order placement

**Context:** OmniScript checkout

**Problem:** Full flow 15s; browser timed out

**Solution:**

Sync IP creates pending order + PE; async worker IP completes; UI polls status

**Why it works:** Fast perceived response


---

## Example 2: Parallel enrichment

**Context:** Credit + address verification

**Problem:** Sequential was 6s total

**Solution:**

IP parallel HTTP calls reduce to 3.5s

**Why it works:** Wall-clock optimization

