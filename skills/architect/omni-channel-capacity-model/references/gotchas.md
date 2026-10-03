# Gotchas: Omni-Channel Capacity Model

Non-obvious platform behaviours that make a capacity model route the wrong amount of work. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Metadata API" means the Metadata API Developer Guide, Version 67.0; "Object Reference" means the Object Reference, Version 67.0. Cross-channel priority and presence-status design are covered in `architect/multi-channel-service-architecture`; this file stays on capacity.

## Gotcha 1: Capacity Is Taken At Assignment, Before The Agent Accepts

**What happens:** Omni-Channel creates an `AgentWork` record with status `Assigned` and pushes it to the agent. The agent's capacity changes at that point: `UserServicePresence.AverageCapacity` and `IdleDuration` are "updated when the agent's capacity changes, such as when the agent is assigned, declines, or closes a work item." While a push sits unanswered, the agent looks fuller than they are. If pushes time out (`DeclinedOnPushTimeout`) or are declined, capacity was tied up for nothing.

**When it occurs:** High-volume periods with long push timeouts and frequent declines.

**How to avoid:** Keep `pushTimeout` on the routing configuration short and set `presenceStatusOnPushTimeout` on the presence configuration so an unresponsive agent leaves the pool. Monitor `AgentWork` rows with status `Declined` and `DeclinedOnPushTimeout`. The earlier "10 to 15 seconds" timeout is a practitioner starting point, not a platform default.

**Source:** Object Reference, AgentWork (Usage: "When AgentWork records are created, they have the status Assigned. After a record is created, it's automatically pushed to the assigned agent"; `Status` values `Assigned`, `Declined`, `DeclinedOnPushTimeout`; `PushTimeoutDateTime`) and UserServicePresence (`AverageCapacity`, `IdleDuration` descriptions). Metadata API, QueueRoutingConfig (`pushTimeout`) and PresenceUserConfig (`presenceStatusOnPushTimeout`).

---

## Gotcha 2: A Live Presence Session Records The Capacity It Started With

**What happens:** An administrator raises `PresenceUserConfig.capacity` from 10 to 15 mid-shift and expects agents to take more work immediately. Each presence session is a `UserServicePresence` record carrying `ConfiguredCapacity` ("The user's total configured primary capacity") and `ConfiguredInterruptCapacity`, so the value in force is the one on the agent's current session row. UNVERIFIED (2026-10-03): this skill's earlier statement that agents must go offline and back online before a changed capacity applies comes from Salesforce Help, which does not fetch; the fields above are the way to check.

**When it occurs:** Capacity tuning during business hours.

**How to avoid:** Change capacity at shift boundaries. After the change, query `UserServicePresence` where `IsCurrentState = true` and compare `ConfiguredCapacity` with the new value; ask agents whose sessions still show the old value to cycle their presence.

**Source:** Object Reference, UserServicePresence (`ConfiguredCapacity`, `ConfiguredInterruptCapacity`, `IsCurrentState`, `StatusStartDate`). Metadata API, PresenceUserConfig (`capacity`: "The maximum number of work units an agent can be assigned at one time").

---

## Gotcha 3: Interruptible Work Uses A Separate Capacity Pool, Set On The Channel

**What happens:** Designers look for an "interruptible" checkbox on the presence configuration. Interruptibility is a property of the work: `ServiceChannel.isInterruptible` "Indicates whether a work item consumes interruptible or primary capacity." The agent's limit for that pool is `PresenceUserConfig.interruptibleCapacity` ("the maximum number of work units using interruptible capacity that can be pushed to an agent at a time"; empty means the same as `capacity`). A routing configuration can override the channel with `capacityType` (`INHERITED`, `INTERRUPTIBLE`, `NOT INTERRUPTIBLE`). This corrects the earlier version of this skill, which placed the interruptible flag on the presence configuration. UNVERIFIED (2026-10-03): the earlier claim that an interrupted item "stays assigned" and must be resumed manually is from Salesforce Help only.

**When it occurs:** Blended voice and messaging designs, and orgs that never enabled the Interruptible Capacity feature (the fields exist only from API 57.0 when it is on).

**How to avoid:** Decide per channel which work is interruptible, set `isInterruptible` on the service channel, size `interruptibleCapacity` separately from `capacity`, and use `capacityType` only where one queue must behave differently from the channel default. Track `UserServicePresence.ConfiguredInterruptCapacity` to confirm agents received it.

**Source:** Metadata API, ServiceChannel (`isInterruptible`, API 57.0+ "when the Interruptible Capacity feature is enabled"); PresenceUserConfig (`interruptibleCapacity`); QueueRoutingConfig (`capacityType` values and behaviour). Object Reference, UserServicePresence (`ConfiguredInterruptCapacity`).

---

## Gotcha 4: Skills Fall Back Only When They Are Marked Additional

**What happens:** A work item requires a language skill that no online agent holds, and it waits even while skilled-for-everything-else agents sit idle. Required skills do not relax. Skills marked Additional Skill do: after `dropAdditionalSkillsTimeout` seconds they are "dropped from Omni-Channel routing and the case is routed to the best-matched agent, even if the agent doesn't have all the skills." This corrects the earlier statement that there is no built-in way to degrade gracefully.

**When it occurs:** Niche skills held by one or two agents, out of hours, and holidays.

**How to avoid:** Mark nice-to-have skills as Additional and set `dropAdditionalSkillsTimeout` on the routing configuration. For skills that must not be dropped, design an overflow path (`queueOverflowAssignee` or `userOverflowAssignee` on the routing configuration) and keep at least three agents per required skill. If the request sets `CustomRequestedDateTime` on the `PendingServiceRouting`, the timeout starts from that time.

**Source:** Metadata API, QueueRoutingConfig (`dropAdditionalSkillsTimeout` description including the `CustomRequestedDateTime` rule; `isAttributeBased`; `queueOverflowAssignee`; `userOverflowAssignee`; `QueueRoutingConfigSkill`).

---

## Gotcha 5: Tab-Based Or Status-Based Is Chosen Per Service Channel, Not Per Agent

**What happens:** The earlier version of this skill said the capacity model is set on the presence configuration and cannot differ by channel. It is set on each service channel: `capacityModel` `TAB_BASED` "releases an agent's capacity when a work tab is closed in the service console"; `STATUS_BASED` keeps work "assigned and applied to an agent's capacity until the work is completed or reassigned." One agent can hold tab-based messaging and status-based case work at once. Tab-based case work frees capacity when an agent closes a tab on an unfinished case.

**When it occurs:** Case and email channels where work spans sessions, and reports comparing `AgentWork.ActiveTime` across channels: active time "is tracked only for tasks routed using the tab-based capacity model."

**How to avoid:** Choose the model per channel. For status-based channels, set `statusField` and map its values to `IN_PROGRESS`, `PAUSED`, and `COMPLETED`. Paused capacity (`PausedCapacityWeight`, `PausedCapacityPercentage`) needs status-based capacity and Enhanced Omni-Channel. A phased migration can go channel by channel.

**Source:** Metadata API, ServiceChannel (`capacityModel` values and descriptions, API 65.0+; `statusField`; `serviceChannelStatusFieldMappings`; `ServiceChannelFieldPriority` `type` values); QueueRoutingConfig (`PausedCapacityWeight`, `PausedCapacityPercentage`, API 64.0+). Object Reference, AgentWork (`CapacityModel` values `StatusBased`, `TabBased`; `ActiveTime`).

---

## Gotcha 6: Weights Live On The Routing Configuration, So One Channel Can Carry Several Weights

**What happens:** The earlier version of this skill described a "capacity weight" on each service channel. The weight is on `QueueRoutingConfig` (`capacityWeight` or `capacityPercentage`), and the agent's total is on `PresenceUserConfig` (`capacity`). Two queues that route cases through different routing configurations can charge different weights for the same kind of case, and changing "the case weight" in one place leaves the other unchanged.

**When it occurs:** Orgs with many queues built over time, each with its own routing configuration.

**How to avoid:** Document capacity per routing configuration and audit them together: list every `QueueRoutingConfig` with its weight or percentage and the queues using it. Keep one routing configuration per work type unless a different weight is intended.

**Source:** Metadata API, QueueRoutingConfig (`capacityWeight`: "The amount of an agent's capacity for work items that's consumed by a work item from this service channel"; `capacityPercentage`); PresenceUserConfig (`capacity`). Object Reference, AgentWork (`CapacityWeight`, `CapacityPercentage` recorded per work item).

---

## Gotcha 7: Voice Must Consume All Of An Agent's Capacity, So Its Weight Moves With The Total

**What happens:** Voice routing configurations must take the whole agent: "Voice calls must have a capacity percentage of 100" and "Voice calls must use the entire capacity weight." A team raises agent capacity from 10 to 15 for more case concurrency but leaves the voice weight at 10, breaking the rule the platform states. An agent on a call "doesn't receive new work items until the call ends."

**When it occurs:** Any capacity change on blended voice agents, and designs that hope agents will answer chats during calls.

**How to avoid:** Express voice as `capacityPercentage` 100 so it tracks any total, or change the voice `capacityWeight` in the same release as `PresenceUserConfig.capacity`. Staff voice peaks separately; use after-conversation work settings for wrap-up rather than lower voice weights.

**Source:** Metadata API, QueueRoutingConfig (`capacityPercentage` and `capacityWeight` voice rules). Object Reference, AgentWork (`CapacityPercentage`: "Voice calls must have a capacity percentage of 100, so an agent on a call doesn't receive new work items until the call ends").

---

## Gotcha 8: Work Assigned Outside Omni-Channel Consumes No Capacity

**What happens:** Supervisors reassign cases by changing the owner, or automation assigns records directly to users. Those records never count against the agent's capacity: "A work item consumes agent capacity only if it was first assigned to the agent by Omni-Channel using queues or skills." Omni-Channel keeps pushing new work to an agent who is already buried.

**When it occurs:** Manual reassignment during escalations, assignment rules or flows that set the owner to a user, and record transfers outside the Omni-Channel widget.

**How to avoid:** Route reassignments through queues or skills so Omni-Channel creates the `AgentWork`. For status-based channels, review `doesCheckCapOnOwnerChange` and `doesCheckCapOnStatusChange`, which control capacity checks when work is reassigned or reopened. Report on records owned by agents with no matching open `AgentWork`.

**Source:** Object Reference, AgentWork (note in the field table beside `CapacityModel`: "A work item consumes agent capacity only if it was first assigned to the agent by Omni-Channel using queues or skills"). Metadata API, ServiceChannel (`doesCheckCapOnOwnerChange`, `doesCheckCapOnStatusChange`, API 65.0+).
