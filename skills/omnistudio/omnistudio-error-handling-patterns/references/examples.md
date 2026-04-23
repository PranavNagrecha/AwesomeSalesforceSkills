# OmniStudio Error Handling — Examples

## Example 1: Fail-Fast IP With Fault Screen

**Context:** OmniScript submits a policy change via an IP that writes to Salesforce and to a downstream policy system.

**Solution:**
- IP step `Update_Policy_SF` → `Fail On Step Error = true`, `Response Action = Terminate IP`.
- IP step `Push_To_Downstream` → same.
- OmniScript branches on IP response `errors` node to a fault screen that lists what failed and offers a retry.

**Why it works:** Half-writes cannot ship; user always sees truth.

---

## Example 2: Best-Effort Enrichment

**Context:** An IP fetches a third-party credit score to display. Service is flaky.

**Solution:** Enrichment step set to `Continue on Error`, with a default `creditScore = "unavailable"`. Downstream reads tolerate the default.

---

## Anti-Pattern: Retry Without Correlation ID

An OmniScript retry button re-invokes the IP. The downstream system sees two distinct POSTs because nothing identifies them as the same logical operation. Result: duplicate records. Always include a correlation ID generated on first attempt and carried through retries.
