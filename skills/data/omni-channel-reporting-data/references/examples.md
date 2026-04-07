# Examples — Omni-Channel Reporting Data

## Example 1: Historical Case-Routed Assignment Report

**Scenario:** A service manager needs a monthly report showing how long routed cases waited before acceptance and how long agents actively handled them.
**Problem:** A generic Omni report design does not preserve the Case-specific context needed for historical reporting.
**Solution:** Create a Custom Report Type for the case-routed channel by joining AgentWork to Case. Expose `RequestDateTime`, `AcceptDateTime`, `CloseDateTime`, `WaitTime`, `HandleTime`, `ActiveTime`, `CapacityWeight`, and `DeclineReason`, then build a summary report grouped by the dimensions the business needs. If a quick data check is needed first, query AgentWork directly:
```sql
SELECT RequestDateTime, AcceptDateTime, CloseDateTime, WaitTime, HandleTime, ActiveTime, CapacityWeight, DeclineReason
FROM AgentWork
WHERE AcceptDateTime = LAST_N_DAYS:30
```
**Why:** AgentWork stores the per-assignment metrics, and the researched notes state that historical reporting requires channel-specific Custom Report Types joining AgentWork to Case, MessagingSession, or VoiceCall (AgentWork Object Reference; Omni Supervisor PDF).

## Example 2: Capacity Utilization Design For Supervisors

**Scenario:** An operations lead wants to understand how much time agents spend in presence statuses compared with the work they actually handle.
**Problem:** Looking only at handled assignments gives work timing, but it does not explain how long agents were available or in other statuses.
**Solution:** Use UserServicePresence as the historical source for presence-status durations, and use AgentWork separately for wait, handle, and active-time analysis. Present the two views together in a dashboard or export so the team can compare status duration with handled workload without collapsing them into one object model.
**Why:** The researched notes identify UserServicePresence as the source that tracks agent presence status durations for capacity utilization, while AgentWork tracks the assignment metrics (UserServicePresence Object Reference; AgentWork Object Reference).

## Example 3: Reporting Correctly After Transfers

**Scenario:** A contact center sees a spike in assignment counts during a week with many transferred conversations.
**Problem:** The team assumes one AgentWork row equals one customer interaction, so the report appears to overcount work.
**Solution:** Keep the report at assignment grain and label the metric accordingly. Add a design note that transferred and abandoned work can generate additional AgentWork records, and create a separate derived metric only if the business truly wants conversation-level volume rather than assignment volume.
**Why:** The researched notes explicitly state that abandoned and transferred work each generate new AgentWork records, so raw row counts must be interpreted as assignment counts unless a separate business rule is applied (AgentWork Object Reference; Omni Supervisor PDF).
