# LLM Anti-Patterns — FSL Optimization Architecture

Common mistakes AI coding assistants make when generating or advising on FSL Optimization Architecture.

## Anti-Pattern 1: Designing Territories Over 50 Resources Without Noting Performance Impact

**What the LLM generates:** Territory designs with 80–120 resources per territory for administrative convenience, without noting the optimization timeout risk.

**Why it happens:** LLMs optimize for organizational clarity without knowing the FSL optimization engine's per-territory performance constraint.

**Correct pattern:** Design territories with a maximum of 50 resources and 1,000 SA/day. Split larger areas into geographic sub-territories. Document the performance constraint as an architectural requirement.

**Detection hint:** Any territory design over 50 resources without a note about Global optimization timeout risk is incomplete.

---

## Anti-Pattern 2: Recommending All-At-Once ESO Adoption

**What the LLM generates:** "Enable ESO for all territories in Setup > Field Service > Enhanced Scheduling. This will immediately improve optimization performance."

**Why it happens:** LLMs default to complete feature adoption instructions without modeling the risk of ESO having no automatic fallback.

**Correct pattern:** Recommend phased ESO adoption: pilot 2–3 territories, validate for 2–3 weeks, then expand territory-by-territory. Document manual dispatch contingency for all ESO-enrolled territories.

**Detection hint:** Any ESO adoption guidance that doesn't mention phased rollout and the no-fallback risk is missing critical architectural context.

---

## Anti-Pattern 3: Not Noting Global Optimization's Silent Timeout Failure

**What the LLM generates:** Instructions to schedule Global optimization nightly without any mention of monitoring job completion or the 2-hour timeout.

**Why it happens:** LLMs assume failures are exception-raised. FSL Global optimization timeouts are silent — no exception, no alert.

**Correct pattern:** Include monitoring as a required component of any Global optimization design: schedule a report or Flow that checks optimization job status each morning and alerts dispatchers if any job shows non-Completed status.

**Detection hint:** Any Global optimization setup guide without a monitoring or alerting component is incomplete.

---

## Anti-Pattern 4: Recommending Concurrent Optimization Without Checking for Shared Resources

**What the LLM generates:** Optimization scheduling that runs Global jobs for all territories simultaneously at the same time.

**Why it happens:** LLMs don't model the cross-territory resource sharing constraint that makes concurrent optimization problematic.

**Correct pattern:** Before recommending concurrent optimization, check whether territories share resources via Secondary ServiceTerritoryMember. Territories sharing resources must be optimized sequentially.

**Detection hint:** Any optimization schedule that runs multiple territories simultaneously without confirming they don't share resources is potentially problematic.

---

## Anti-Pattern 5: Treating ESO as a Global Setting (Not Per-Territory)

**What the LLM generates:** Instructions to enable ESO in Setup as a global org-wide setting that affects all territories.

**Why it happens:** Many Salesforce features are global org settings. ESO is specifically per-territory.

**Correct pattern:** ESO is enabled and managed per service territory in Setup > Field Service > Enhanced Scheduling. Each territory's ESO enrollment must be explicitly configured. Some territories can use ESO while others continue on the legacy engine.

**Detection hint:** Any ESO guidance that treats it as a single org-wide toggle is incorrect.
