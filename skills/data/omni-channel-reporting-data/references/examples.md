# Examples: Omni-Channel Reporting Data

Field names below come from the Object Reference (Summer '26) entries for AgentWork, UserServicePresence, and PendingServiceRouting. The `Type` qualifier on a polymorphic field comes from the SOQL and SOSL Reference ("Using the Type Qualifier").

## Example 1: Historical Case-Routed Assignment Metrics

**Scenario:** A service manager needs a monthly view of how long routed cases waited before acceptance and how long agents handled them.

**Problem:** The first draft selected `WaitTime` from AgentWork and failed to compile. AgentWork has no `WaitTime`; the request-to-accept interval is `SpeedToAnswer`.

**Solution:** Query AgentWork filtered to Case work items. Save as `soql/agentwork_case_last_month.soql` in the reporting repo:

```sql
SELECT Id, WorkItemId, UserId, OriginalGroup.Name, ServiceChannel.DeveloperName,
       RequestDateTime, AssignedDateTime, AcceptDateTime, CloseDateTime,
       SpeedToAnswer, HandleTime, ActiveTime, CapacityModel,
       CapacityWeight, CapacityPercentage, Status, DeclineReason
FROM AgentWork
WHERE WorkItem.Type = 'Case'
  AND CloseDateTime = LAST_MONTH
ORDER BY CloseDateTime
```

**Why:** Every field is on AgentWork. `HandleTime` is CloseDateTime minus accept time, so filtering on `CloseDateTime` keeps the metric to finished work. `ActiveTime` is meaningful only where `CapacityModel = 'TabBased'`.

## Example 2: Conversation Count That Survives Transfers

**Scenario:** A contact center sees assignment counts spike during a week with many transfers.

**Problem:** The team counted AgentWork rows, and each transfer created another row.

**Solution:** Count distinct work items for conversation volume, and keep row counts labeled as assignments:

```sql
SELECT COUNT_DISTINCT(WorkItemId) conversations, COUNT(Id) assignments
FROM AgentWork
WHERE WorkItem.Type = 'MessagingSession'
  AND RequestDateTime = LAST_WEEK
```

**Why:** "If the work is transferred to another agent, a new AgentWork record is created." `IsTransfer` would split the two directly, but it is readable only in reports, not through SOQL.

## Example 3: Completed Presence Time Per Agent

**Scenario:** An operations lead wants hours in each presence status for yesterday.

**Problem:** A draft summed `StatusDuration` for all of yesterday's rows. Agents who stayed online past midnight had no duration on their open row.

**Solution:** Sum only completed rows, grouped by status:

```sql
SELECT UserId, ServicePresenceStatus.DeveloperName, SUM(StatusDuration) secondsInStatus,
       SUM(IdleDuration) secondsIdle, SUM(AtCapacityDuration) secondsAtCapacity
FROM UserServicePresence
WHERE StatusStartDate = YESTERDAY
  AND StatusEndDate != null
GROUP BY UserId, ServicePresenceStatus.DeveloperName
```

**Why:** `StatusDuration` is "set only when the current user service presence status ends." Open rows (`IsCurrentState = true`) must be computed separately as now minus `StatusStartDate`. UNVERIFIED (2026-10-03): the relationship name `ServicePresenceStatus` is inferred from the `ServicePresenceStatusId` field; the Object Reference entry lists the field but not the relationship name. If it fails, group by `ServicePresenceStatusId`.

## Example 4: Live Backlog by Queue

**Scenario:** A supervisor wants the number of items waiting per queue right now.

**Solution:**

```sql
SELECT Group.Name, ServiceChannel.DeveloperName, COUNT(Id) waiting
FROM PendingServiceRouting
WHERE IsReadyForRouting = true
GROUP BY Group.Name, ServiceChannel.DeveloperName
```

**Why:** PendingServiceRouting represents work "waiting to be routed or assigned," so it answers the "now" question and not the historical one. `GroupId` replaces the no-longer-recommended `QueueId`. UNVERIFIED (2026-10-03): the relationship name `Group` for `GroupId` is inferred; if it fails, group by `GroupId`.
