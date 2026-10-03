# Gotchas: Omni-Channel Reporting Data

Non-obvious behaviours that make Omni-Channel reports wrong, empty, or impossible to build. Each gotcha names its source. "Object Reference" means the Salesforce Object Reference, Summer '26 (object_reference.pdf). "SOQL Guide" means the SOQL and SOSL Reference, Summer '26. "Omni Supervisor guide" means the Omni Supervisor PDF, Spring '26.

## Gotcha 1: AgentWork Has No WaitTime Field

**What happens:** A query such as `SELECT WaitTime FROM AgentWork` fails with "No such column 'WaitTime'". A report spec that promises "average wait time from AgentWork" cannot be built as written.

**When it occurs:** Teams copy the field name from chat reporting. `WaitTime` is a LiveChatTranscript field ("The total amount of time in seconds a chat request was waiting to be accepted by an agent"), not an AgentWork field.

**How to avoid:** Use `SpeedToAnswer` ("The amount of time between when the work was requested and when an agent accepted it") for request-to-accept. Use `AssignedDateTime - RequestDateTime` if the business means time in queue before the push. Name the interval on every dashboard tile.

**Source:** Object Reference, AgentWork fields (no WaitTime between UserId and WorkItemId; SpeedToAnswer, RequestDateTime, AssignedDateTime) and LiveChatTranscript fields (WaitTime).

---

## Gotcha 2: Transfers Create New Rows, and IsTransfer Is Not Available Through the API

**What happens:** Weekly assignment counts jump after a reorganization that increased transfers. Someone tries to filter `WHERE IsTransfer = false` in SOQL or a data export and gets an error or an empty column.

**When it occurs:** Any transfer: "If the work is transferred to another agent, a new AgentWork record is created." `IsTransfer` and `IsConference` are documented as "accessible in Reports, but not via the API."

**How to avoid:** Decide the grain first. For conversation counts through the API, count distinct `WorkItemId`. For a first-assignment versus transfer split, build the report on an AgentWork report type where `IsTransfer` is available, or use `Status = 'Transferred'` on the row that was handed off. `TransferRequesterId` (API 63.0+) is populated only on the reassigned row, not the original.

**Source:** Object Reference, AgentWork description; IsTransfer and IsConference field notes; Status picklist (Transferred); TransferRequesterId description.

---

## Gotcha 3: ActiveTime Is Empty for Status-Based Capacity

**What happens:** Average active time per agent looks far too low, or many rows show no active time at all.

**When it occurs:** The channel uses status-based capacity. "Active time is tracked only for tasks routed using the tab-based capacity model. It's tracked only when the work tab is open and in focus in the console." Switching console tabs pauses it; switching browser tabs does not.

**How to avoid:** Group or filter by `CapacityModel` (StatusBased or TabBased, API 50.0+). Report `ActiveTime` only for TabBased rows and use `HandleTime` for the rest. Document that ActiveTime measures focus time, not effort.

**Source:** Object Reference, AgentWork ActiveTime and CapacityModel fields.

---

## Gotcha 4: StatusDuration Is Null Until the Status Ends

**What happens:** A utilization dashboard run at 2 p.m. shows almost no online time for agents who have been Available since 8 a.m.

**When it occurs:** `StatusDuration` and `StatusEndDate` are "set only when the current user service presence status ends, such as when the agent changes to another presence status or logs out." The open row has `IsCurrentState = true` and no duration.

**How to avoid:** Sum `StatusDuration` only for closed rows (`StatusEndDate != null`), and compute open rows separately as now minus `StatusStartDate` if the business wants live totals. Do not build automation on presence changes with Apex: "Apex triggers aren't supported with UserServicePresence." Supervisors who set an agent to Offline from Omni Supervisor stop tracking: "If you select Offline, keep in mind that the agent's work isn't tracked anymore."

**Source:** Object Reference, UserServicePresence StatusDuration, StatusEndDate, IsCurrentState, Usage. Omni Supervisor guide, Agents Tab (All Agents subtab).

---

## Gotcha 5: PendingServiceRouting Is a Live Backlog, Not History

**What happens:** A "backlog trend for last quarter" built on PendingServiceRouting shows the work that is waiting now, not what waited last quarter.

**When it occurs:** PendingServiceRouting "represents the routing details of a work item that's waiting to be routed or assigned." It describes the queue as it stands. UNVERIFIED (2026-10-03): whether the record is removed once the AgentWork is created is not stated in a fetched source; test in your org before relying on either behaviour.

**How to avoid:** Use PendingServiceRouting for "what is waiting right now" and AgentWork (`RequestDateTime`, `AssignedDateTime`, `SpeedToAnswer`) for history. Join them through `AgentWork.PendingServiceRoutingId` (API 50.0+) when you need routing attributes on a historical row. Watch the org's Pending Service Routing usage on the Omni-Channel Limits page in Setup.

**Source:** Object Reference, PendingServiceRouting description and Limits section; AgentWork PendingServiceRoutingId field.

---

## Gotcha 6: OriginalQueueId Is No Longer Recommended

**What happens:** Queue-level reports built years ago on `OriginalQueueId` behave inconsistently or stop matching the queue shown in Omni Supervisor.

**When it occurs:** "Due to API changes, OriginalQueueId is no longer recommended. Use OriginalGroupId instead." The same note applies to `PendingServiceRouting.QueueId` versus `GroupId`.

**How to avoid:** Group by `OriginalGroupId` (relationship `OriginalGroup`) in new queries and report types, and migrate old ones. Remember the original queue is where the work was first routed, not where it was closed after a transfer.

**Source:** Object Reference, AgentWork OriginalQueueId and OriginalGroupId; PendingServiceRouting QueueId and GroupId.

---

## Gotcha 7: Live Supervisor Metrics and Historical Analytics Are Different Concerns

**What happens:** A supervisor compares the Omni Supervisor "Handle Time" column with a historical report and the numbers disagree.

**When it occurs:** Omni Supervisor shows real-time state. Its Handle Time is "the difference between 'now' and when the agent accepted the work," while AgentWork `HandleTime` is CloseDateTime minus accept time on a finished row. The Agent Timeline shows AgentWork status, not the work item's own status.

**How to avoid:** Use Omni Supervisor for live monitoring and AgentWork plus UserServicePresence for history. Label historical tiles "closed work only" when they use `HandleTime`.

**Source:** Omni Supervisor guide, Agents Tab and Agent Detail Fields (Handle Time, Requested Time, Assigned Time, Accepted Time). Object Reference, AgentWork HandleTime.
