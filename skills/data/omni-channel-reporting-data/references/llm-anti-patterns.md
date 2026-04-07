# LLM Anti-Patterns — Omni-Channel Reporting Data

Common mistakes AI coding assistants make when generating or advising on Omni-Channel reporting data models.

## Anti-Pattern 1: Designing One Universal Historical Report Type

**What the LLM generates:** "Create one Omni-Channel Custom Report Type that joins AgentWork to every routed object so cases, messaging, and voice can all be reported together."
**Why it happens:** The model optimizes for simplification and ignores the researched note that historical reporting is channel specific.
**Correct pattern:** Create separate historical report types by channel: AgentWork to Case, AgentWork to MessagingSession, and AgentWork to VoiceCall as needed.
**Detection hint:** Reviewer checklist item: does the design claim a single CRT works for Case, MessagingSession, and VoiceCall together?

## Anti-Pattern 2: Treating AgentWork Rows As Customer Interactions

**What the LLM generates:** "Count AgentWork rows to get total conversations handled."
**Why it happens:** The model assumes one record represents one end-to-end interaction.
**Correct pattern:** Treat AgentWork as assignment grain and document that transferred and abandoned work can create new AgentWork rows. Only build conversation-level counting as a separate derived rule.
**Detection hint:** Grep for phrases like `total conversations = AgentWork count` or `one row per interaction`.

## Anti-Pattern 3: Computing Capacity Utilization Only From AgentWork

**What the LLM generates:** "Use HandleTime and ActiveTime from AgentWork to calculate agent capacity utilization."
**Why it happens:** The model conflates handled-assignment timing with presence-status duration.
**Correct pattern:** Use UserServicePresence for presence-duration utilization analysis and AgentWork for assignment timing. Combine them only in the final reporting layer.
**Detection hint:** Search for `capacity utilization` in output that references `AgentWork` but never mentions `UserServicePresence`.

## Anti-Pattern 4: Recomputing Timing That Salesforce Already Tracks

**What the LLM generates:**
```sql
SELECT RequestDateTime, AcceptDateTime, CloseDateTime FROM AgentWork
```
Deriving wait duration only from timestamps while ignoring the stored timing metrics.
**Why it happens:** The model defaults to timestamp subtraction patterns from generic SQL training data.
**Correct pattern:** Prefer the documented AgentWork metrics for reporting where available: `WaitTime`, `HandleTime`, and `ActiveTime`, and keep the timestamps for timeline context only.
**Detection hint:** Grep for output that selects only `RequestDateTime`, `AcceptDateTime`, and `CloseDateTime` while omitting `WaitTime`, `HandleTime`, and `ActiveTime` in a timing report.

## Anti-Pattern 5: Ignoring Transfer And Abandon Effects In Totals

**What the LLM generates:** "A spike in row count means the team handled more demand."
**Why it happens:** The model treats row growth as workload growth without checking event semantics.
**Correct pattern:** Check whether transfers or abandons increased the number of AgentWork records before interpreting row-count increases as demand growth.
**Detection hint:** Reviewer checklist item: does the metric definition mention how transfers and abandons affect counts?

## Anti-Pattern 6: Using Omni Supervisor As The Historical Data Model

**What the LLM generates:** "Take queue wait time and agent capacity directly from Omni Supervisor and treat that as the historical source."
**Why it happens:** The UI is highly visible, so the model mistakes operational monitoring surfaces for stored analytical data.
**Correct pattern:** Use Omni Supervisor to understand live operational views, but build historical analytics from AgentWork, UserServicePresence, and the required channel-specific report types.
**Detection hint:** Search for plans based on screenshots, wallboards, or supervisor tabs without any mention of AgentWork or UserServicePresence.
