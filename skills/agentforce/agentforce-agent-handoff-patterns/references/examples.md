# Agentforce Agent Handoff — Examples

## Example 1: Structured Escalation With Summary

**Context:** Service agent cannot resolve a refund request above the agent's authority.

**Procedure:**
- Agent creates a Case with structured fields: `UserIntent`, `SummaryOfAttempt`, `RequestedRefundAmount`, `PolicyConflictReason`.
- Case routes to Omni-Channel queue `Tier2_Refunds`.
- Agent says: "I'm connecting you to a specialist. They'll see a summary of what we've discussed so you don't need to repeat yourself. Estimated wait: 3 minutes."

**Why it works:** Human agent opens the case, sees summary, continues without "tell me the whole story."

---

## Example 2: Confidence-Triggered Escalation

Agent attempts to resolve a password reset twice; both fail (user enters unknown email). On third attempt, a confidence-triggered escalation fires: "I'm having trouble with this. Let me connect you with support."

Avoids the infinite-retry loop users hate.

---

## Example 3: Deflection-With-Recommendation

Out-of-hours, queue is empty, user asks a niche question. Agent says: "I can't connect you to a specialist right now. Please visit [link] or I can schedule a callback for tomorrow morning."

---

## Anti-Pattern: Raw Transcript In Case Description

A team packaged the full verbatim conversation (sometimes 30+ turns) into the Case description. Human agents dreaded opening these cases. Fix: send a link to the transcript, and a structured summary.
