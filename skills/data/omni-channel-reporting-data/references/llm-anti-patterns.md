# LLM Anti-Patterns — Omni-Channel Reporting Data

Common mistakes AI coding assistants make when generating or advising on Omni-Channel reporting data models.

## Anti-Pattern 1: Designing One Universal Historical Report Type

**What the LLM generates:** "Create one Omni-Channel Custom Report Type that joins AgentWork to every routed object so cases, messaging, and voice can all be reported together."
**Why it happens:** The model optimizes for simplification and ignores that `AgentWork.WorkItemId` is polymorphic, so each channel's business fields live on a different object.
**Correct pattern:** Keep one reporting design per channel: AgentWork filtered by `WorkItem.Type` or by service channel, plus that channel's own fields. Whether each channel needs its own custom report type is UNVERIFIED (2026-10-03); an AgentWork-based report type filtered by `ServiceChannel` is the grounded starting point.
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

## Anti-Pattern 4: Selecting a WaitTime Field From AgentWork

**What the LLM generates:**
```sql
SELECT RequestDateTime, AcceptDateTime, WaitTime, HandleTime FROM AgentWork
```
**Why it happens:** The model borrows `WaitTime` from LiveChatTranscript or from generic contact-center vocabulary. AgentWork has no such field, so the query fails to compile.
**Correct pattern:** Use the stored AgentWork metrics: `SpeedToAnswer` for request-to-accept, `HandleTime` for accept-to-close, and `ActiveTime` for focus time on tab-based channels. Keep `RequestDateTime`, `AssignedDateTime`, `AcceptDateTime`, and `CloseDateTime` for timeline context.
**Detection hint:** `scripts/check_omni_channel_reporting_data.py` raises `OMNI-FIELD-01` for `WaitTime` in any AgentWork query.

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

## Anti-Pattern 7: Summing StatusDuration Across Open and Closed Presence Rows

**What the LLM generates:** `SELECT UserId, SUM(StatusDuration) FROM UserServicePresence WHERE StatusStartDate = TODAY GROUP BY UserId` presented as "online time today."
**Why it happens:** The model assumes the duration is maintained continuously. `StatusDuration` is set only when the status ends, so every agent who is still online contributes nothing.
**Correct pattern:** Filter `StatusEndDate != null` for completed periods, and compute open rows (`IsCurrentState = true`) as now minus `StatusStartDate` in the reporting layer if live totals are required.
**Detection hint:** `OMNI-USP-01` in the checker flags a `StatusDuration` aggregate without a `StatusEndDate` or `IsCurrentState` filter.

## Anti-Pattern 8: Filtering on IsTransfer in SOQL

**What the LLM generates:** `SELECT COUNT() FROM AgentWork WHERE IsTransfer = false` to count first assignments.
**Why it happens:** The field exists in the Object Reference, so the model assumes it is queryable. The reference says it is "accessible in Reports, but not via the API."
**Correct pattern:** Count distinct `WorkItemId` for conversation volume through the API, or use a report built on an AgentWork report type where `IsTransfer` is available as a column.
**Detection hint:** `OMNI-API-01` in the checker flags `IsTransfer` or `IsConference` in SOQL and Apex.

