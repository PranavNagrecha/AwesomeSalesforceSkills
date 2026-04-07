---
name: omni-channel-reporting-data
description: "Omni-Channel analytics data: agent work records, queue metrics, capacity utilization, wait time reporting. NOT for admin routing setup."
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
inputs:
  - "Which service channels are in scope: Case, MessagingSession, VoiceCall, or a subset"
  - "Whether the request is for assignment-level metrics, presence utilization, or both"
  - "What reporting output is needed: native report, dashboard, or exported dataset"
  - "How the business wants to treat transferred and abandoned work in totals"
outputs:
  - "Channel-specific reporting design for AgentWork joined to the correct work item object"
  - "Metric mapping for RequestDateTime, AcceptDateTime, CloseDateTime, WaitTime, HandleTime, ActiveTime, CapacityWeight, and DeclineReason"
  - "Capacity utilization approach using UserServicePresence duration data"
  - "Data interpretation rules for transfers, abandons, and assignment counts"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

Omni-Channel reporting questions become tractable once you separate assignment history from presence history and choose the exact service channel you are analyzing. The goal is to produce metrics that match how Salesforce stores work movement: AgentWork for per-assignment timing and UserServicePresence for status-duration capacity analysis. Historical reporting gets reliable only when the design respects channel-specific joins and the fact that transfers and abandons create additional AgentWork rows.

## Before Starting

- Which exact channel needs historical reporting: Case, MessagingSession, VoiceCall, or more than one?
- Is the metric really about handled assignments, or is it about agent presence time and capacity utilization?
- Should transferred and abandoned work count as separate assignment events, or is the business trying to approximate conversation-level volume?

## Core Concepts

### AgentWork Stores Assignment-Level Metrics

AgentWork is the historical record for an Omni-Channel assignment. The researched sources identify `RequestDateTime`, `AcceptDateTime`, `CloseDateTime`, `WaitTime`, `HandleTime`, `ActiveTime`, `CapacityWeight`, and `DeclineReason` as the core fields for understanding how long work waited, when it was accepted, how long it stayed active, and how much capacity it consumed. Use these fields when the question is about assignment timing or workload, not when the question is about how long an agent stayed in a given presence status.

### UserServicePresence Stores Presence Duration History

UserServicePresence is the data source for presence-status duration analysis. That matters because capacity utilization is not just a sum of handled work; it depends on how long agents were in statuses that made them available, away, or otherwise participating in Omni-Channel routing. If the reporting request says "utilization," "status duration," or "time spent available," the design has to include UserServicePresence rather than trying to derive everything from AgentWork alone.

### Historical Reporting Is Channel Specific

The researched notes are explicit that historical Omni-Channel reporting requires Custom Report Types per channel that join AgentWork to the underlying work item object. That means a Case-routed design is different from a MessagingSession-routed design, and a VoiceCall-routed design is different again. A single universal historical report model is the wrong starting point because the related object differs by service channel.

### Transfers and Abandons Change the Row Grain

Transferred and abandoned work do not preserve a single AgentWork row from start to finish. The researched notes state that abandoned and transferred work each generate new AgentWork records. That makes AgentWork an assignment-grain dataset rather than a conversation-grain dataset. If a team counts raw rows without defining the grain, totals can rise for reasons that are operationally correct but analytically surprising.

## Common Patterns

### Channel-Specific Historical Report Types

**When to use:** A stakeholder wants historical wait time, handle time, or active time for a specific Omni-Channel channel.

**How it works:** Build a Custom Report Type for that channel by joining AgentWork to the related work item object: Case, MessagingSession, or VoiceCall. Expose the AgentWork timing and capacity fields, then add the channel-specific business fields needed for grouping and filtering.

**Why not the alternative:** A single generic report type hides the real join requirement and breaks as soon as different channels need different related-object context.

### Capacity Utilization From Presence Plus Work

**When to use:** An operations lead asks for capacity utilization, online time, or time-in-status analysis.

**How it works:** Treat UserServicePresence as the source for status durations and AgentWork as the source for handled-assignment timing. Put the two datasets side by side in the reporting design instead of forcing one object to answer both questions.

**Why not the alternative:** AgentWork can describe assignment timing, but the researched notes point to UserServicePresence for presence-status durations used in utilization analysis.

### Assignment Reporting That Survives Transfers

**When to use:** Reports look inflated after heavy transfer or abandonment activity.

**How it works:** Keep the metric labeled at assignment grain, and document that transferred or abandoned work can create additional AgentWork rows. If leadership needs conversation-level counting, define that as a separate derived metric rather than silently reinterpreting AgentWork rows.

**Why not the alternative:** Pretending each row equals one customer interaction produces misleading totals because Salesforce creates new AgentWork records for transferred and abandoned work.

## Recommended Workflow

1. Confirm the channel scope first, and split the work into separate reporting designs for Case, MessagingSession, and VoiceCall where needed.
2. Map each requested metric to its real source: AgentWork for assignment timing and UserServicePresence for presence-duration utilization.
3. Build the channel-specific Custom Report Type that joins AgentWork to the correct related work item object.
4. Expose and validate the AgentWork fields the analysis depends on: `RequestDateTime`, `AcceptDateTime`, `CloseDateTime`, `WaitTime`, `HandleTime`, `ActiveTime`, `CapacityWeight`, and `DeclineReason`.
5. Define the reporting grain in writing before aggregating anything, and state how transferred and abandoned work will be treated.
6. Test the design with known transfer and abandonment samples so stakeholders can see why row counts and conversation counts are not always the same.
7. Publish the metric definitions alongside the report so supervisors know which measures come from AgentWork and which come from UserServicePresence.
