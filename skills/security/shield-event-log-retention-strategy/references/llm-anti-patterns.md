# LLM Anti-Patterns — Shield Event Log Retention

## Anti-Pattern 1: Proposing Uniform Retention Across All Events

**What the LLM generates:** "Keep all Event Monitoring logs for 7 years in Splunk."

**Why it happens:** Uniform policies are easier to describe.

**Correct pattern:** Tier by event value. High-value events get long retention; low-value events get short retention or sampling.

## Anti-Pattern 2: Treating The Event Monitoring Analytics App As A Backup

**What the LLM generates:** "Event Monitoring Analytics App retains the data, so we're covered."

**Why it happens:** It's the most visible surface.

**Correct pattern:** The analytics app has its own short retention. Assume you need an external archive pipeline.

## Anti-Pattern 3: No Query Runbook

**What the LLM generates:** Detailed retention policy; no guidance on how to actually answer an audit question.

**Why it happens:** Retention feels like the end state.

**Correct pattern:** A runbook documents per-question, per-tier query steps. Test it against a real audit request.

## Anti-Pattern 4: Real-Time Bus Instead Of ELF For Audit

**What the LLM generates:** "Subscribe to the Streaming API events for audit retention."

**Why it happens:** Real-time feels modern.

**Correct pattern:** Real-time is for detection. ELF (batch) is the archival source of record.

## Anti-Pattern 5: Ignoring Ingest Cost

**What the LLM generates:** Architecture with no cost model.

**Why it happens:** Cost feels like procurement's problem.

**Correct pattern:** Model ingest GB/day per event type; cost dominates architecture choices. Split, sample, or tier to control it.
