# Gotchas — Omni-Channel Reporting Data

## Gotcha 1: AgentWork Is Not Conversation Grain

**Behavior:** AgentWork stores per-assignment history, and transferred or abandoned work can create new AgentWork records.
**Why it surprises:** Practitioners often expect one row per case, chat, or call from start to finish.
**Mitigation:** Define the report grain explicitly as assignment-level unless a separate derived conversation metric is being built.

## Gotcha 2: Capacity Utilization Does Not Come From AgentWork Alone

**Behavior:** AgentWork tracks assignment timing, but UserServicePresence tracks the presence-status durations used for capacity utilization analysis.
**Why it surprises:** Many designs assume handled work time is enough to explain utilization, so they never model presence history.
**Mitigation:** Use UserServicePresence for status-duration analysis and AgentWork for handled-assignment metrics, then combine the two only at the reporting layer.

## Gotcha 3: Historical Reporting Must Follow The Service Channel

**Behavior:** Historical Omni-Channel reporting requires Custom Report Types per channel that join AgentWork to Case, MessagingSession, or VoiceCall.
**Why it surprises:** Teams often try to design one universal historical dataset for all routed work.
**Mitigation:** Split the reporting model by channel and build separate report types where the related work item object changes.

## Gotcha 4: Live Supervisor Metrics And Historical Analytics Are Different Concerns

**Behavior:** Omni Supervisor exposes live queue and agent views such as wait-time and capacity indicators, while historical analytics rely on stored object data such as AgentWork and UserServicePresence.
**Why it surprises:** Supervisors see the live UI first and assume it is the historical reporting model too.
**Mitigation:** Use Omni Supervisor to understand operational monitoring, but build historical reporting from the documented object model and channel-specific report types.
