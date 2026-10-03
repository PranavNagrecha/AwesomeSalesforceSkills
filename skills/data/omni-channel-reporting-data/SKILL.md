---
name: omni-channel-reporting-data
description: "Omni-Channel analytics data: agent work records, queue metrics, capacity, wait times. Triggers: Omni-Channel reporting, agent work metrics, queue wait time. NOT for routing/capacity admin setup — use admin/omni-channel-routing-setup. NOT for capacity modeling architecture — use architect/omni-channel-capacity-model."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - omni-channel
  - service-cloud
  - reporting-data
  - agentwork
  - capacity-utilization
  - custom-report-types
triggers:
  - "how do I report Omni wait time historically"
  - "why are transferred chats counted twice"
  - "how can I measure agent capacity utilization"
  - "which object stores accepted Omni work data"
  - "how do I report Omni data by channel"
  - "query AgentWork for speed to answer and handle time by queue"
  - "build an agent utilization report from UserServicePresence status durations"
inputs:
  - "Which service channels are in scope: Case, MessagingSession, VoiceCall, or a subset"
  - "Whether the request is for assignment-level metrics, presence utilization, or both"
  - "What reporting output is needed: native report, dashboard, or exported dataset"
  - "How the business wants to treat transferred and abandoned work in totals"
outputs:
  - "Channel-specific reporting design for AgentWork joined to the correct work item object"
  - "Metric mapping for RequestDateTime, AssignedDateTime, AcceptDateTime, CloseDateTime, SpeedToAnswer, HandleTime, ActiveTime, CapacityWeight, and DeclineReason"
  - "Capacity utilization approach using UserServicePresence duration data"
  - "Data interpretation rules for transfers, abandons, and assignment counts"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

Omni-Channel reporting questions become tractable once you separate assignment history from presence history and choose the exact service channel you are analyzing. The goal is to produce metrics that match how Salesforce stores work movement: AgentWork for per-assignment timing and UserServicePresence for status-duration capacity analysis. Historical reporting gets reliable only when the design respects channel-specific joins and the fact that transfers and abandons create additional AgentWork rows.

## Before Starting

- Which exact channel needs historical reporting: Case, MessagingSession, VoiceCall, or more than one?
- Is the metric really about handled assignments, or is it about agent presence time and capacity utilization?
- Should transferred and abandoned work count as separate assignment events, or is the business trying to approximate conversation-level volume?
- Does the org use tab-based or status-based capacity? `ActiveTime` is tracked only for the tab-based model.

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "When you say wait time, do you mean time to accept, time to assign, or chat queue time?" | AgentWork has no `WaitTime` field; the request-to-accept interval is `SpeedToAnswer`, and `WaitTime` lives on LiveChatTranscript (Gotcha 1) | A named field and a definition per metric | Queries compile, and every tile states which interval it measures |
| "Should a transferred conversation count once or once per agent?" | Each transfer creates a new AgentWork row, and `IsTransfer` is readable in reports but not through the API (Gotcha 2) | An assignment-grain or conversation-grain decision written down | Totals survive heavy transfer weeks without anyone "fixing" the numbers |
| "Is the capacity model tab-based or status-based for each channel?" | `ActiveTime` is tracked only for tab-based routing; status-based rows leave it empty (Gotcha 3) | Per-channel capacity model and which time field to trust | Active-time averages are not dragged down by rows that never had the metric |
| "Do you need today's online time, or only completed status periods?" | `StatusDuration` is set only when a status ends, so an open status has no duration yet (Gotcha 4) | A rule for open sessions (exclude, or compute to now) | Utilization does not silently drop the agents who are online right now |
| "Is the backlog question about now or about last month?" | PendingServiceRouting holds work waiting to be routed; it is a live view, not history (Gotcha 5) | Live backlog from PendingServiceRouting, history from AgentWork | Nobody builds a trend line on an object that only shows the current queue |
| "Which queue should a routed item be credited to?" | `OriginalQueueId` is no longer recommended; `OriginalGroupId` replaces it (Gotcha 6) | The grouping field per report | Queue reports keep working as the API moves on |

## Core Concepts

### AgentWork Stores Assignment-Level Metrics

AgentWork represents a work assignment routed to an agent. Its timing fields are `RequestDateTime` (when the work was requested), `AssignedDateTime` (when it was assigned to an agent), `AcceptDateTime`, `CloseDateTime`, `SpeedToAnswer` (time between request and acceptance), `HandleTime` (CloseDateTime minus accept time), and `ActiveTime` (time the work tab was open and in focus, tab-based capacity only). Workload fields are `CapacityWeight` and `CapacityPercentage`. Outcome fields are `Status` (Assigned, Canceled, Closed, Declined, DeclinedOnPushTimeout, Opened, Transferred, Unavailable), `DeclineReason`, and `DeclineDateTime`. Use these fields when the question is about assignment timing or workload, not when the question is about how long an agent stayed in a presence status.

Correction (2026-10-03): earlier versions of this skill listed `WaitTime` as an AgentWork field. The Object Reference has no such field on AgentWork. `SpeedToAnswer` is the request-to-accept interval, and `WaitTime` belongs to LiveChatTranscript.

### UserServicePresence Stores Presence Duration History

UserServicePresence is the data source for presence-status duration analysis: `StatusStartDate`, `StatusEndDate`, `StatusDuration`, `IdleDuration`, `AtCapacityDuration`, `AverageCapacity`, `ConfiguredCapacity`, `IsAway`, `IsCurrentState`, and `ServicePresenceStatusId`. Capacity utilization depends on how long agents were in statuses that made them available, away, or otherwise participating in routing. If the request says "utilization," "status duration," or "time spent available," the design has to include UserServicePresence rather than deriving everything from AgentWork.

### Historical Reporting Is Channel Specific

`AgentWork.WorkItemId` is polymorphic: one AgentWork table holds Case, MessagingSession, VoiceCall, Lead, and other routed records. A Case-routed design needs Case fields, a messaging design needs MessagingSession fields, and they should not be forced into one model. In SOQL, filter with the `Type` qualifier (`WorkItem.Type = 'Case'`) or by `ServiceChannel.RelatedEntity`. The earlier statement that historical reporting requires one Custom Report Type per channel is UNVERIFIED (2026-10-03): it was not found in the Omni Supervisor guide or the Object Reference. A report type on AgentWork as the base object, filtered by service channel, is a grounded alternative (see `references/metadata-examples.md`).

### Transfers and Abandons Change the Row Grain

"If the work is transferred to another agent, a new AgentWork record is created" (Object Reference, AgentWork). That makes AgentWork an assignment-grain dataset. Canceled requests (for example a chat visitor who leaves before an agent accepts) keep their own row with `Status = Canceled` and a `CancelDateTime`. If a team counts raw rows without defining the grain, totals rise for reasons that are operationally correct but analytically surprising.

## Common Patterns

### Channel-Specific Historical Reporting

**When to use:** A stakeholder wants historical speed to answer, handle time, or active time for one Omni-Channel channel.

**How it works:** Query or report on AgentWork filtered to the channel (`WorkItem.Type = 'Case'` or the service channel), expose the AgentWork timing and capacity fields, then add the channel-specific business fields needed for grouping. `references/examples.md` has the SOQL; `references/metadata-examples.md` has a deployable report type.

**Why not the alternative:** One generic design hides the polymorphic join and breaks as soon as different channels need different related-object context.

### Capacity Utilization From Presence Plus Work

**When to use:** An operations lead asks for capacity utilization, online time, or time-in-status analysis.

**How it works:** Treat UserServicePresence as the source for status durations and AgentWork as the source for handled-assignment timing. Put the two datasets side by side in the reporting design instead of forcing one object to answer both questions. Exclude or separately compute open status rows (`IsCurrentState = true`, `StatusEndDate = null`).

**Why not the alternative:** AgentWork can describe assignment timing, but it does not record how long an agent was Available, Away, or Busy.

### Assignment Reporting That Survives Transfers

**When to use:** Reports look inflated after heavy transfer or abandonment activity.

**How it works:** Keep the metric labeled at assignment grain. For a conversation count, count distinct `WorkItemId` per period instead of rows. In a report built on an AgentWork report type, `IsTransfer` can split first assignments from transfers; through the API it cannot.

**Why not the alternative:** Pretending each row equals one customer interaction produces misleading totals.

## Recommended Workflow

1. Confirm the channel scope first, and split the work into separate reporting designs for Case, MessagingSession, and VoiceCall where needed.
2. Map each requested metric to its real field using the Questions table: `SpeedToAnswer` for wait-to-accept, `HandleTime` and `ActiveTime` for handling, UserServicePresence durations for utilization.
3. Build the query or report type: AgentWork as the base, filtered by channel, with the timing, capacity, and status fields (start from `references/metadata-examples.md`).
4. Define the reporting grain in writing before aggregating, and state how transferred, canceled, and declined work will be treated.
5. Run `python3 scripts/check_omni_channel_reporting_data.py --manifest-dir <your SOQL, Apex and reportTypes folder>` to catch non-existent fields, API-hidden fields, and open-status duration bugs.
6. Test with known transfer and abandonment samples so stakeholders can see why row counts and conversation counts differ.
7. Publish the metric definitions alongside the report so supervisors know which measures come from AgentWork and which from UserServicePresence.
