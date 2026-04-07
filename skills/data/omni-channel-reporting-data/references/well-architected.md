# Well-Architected Notes — Omni-Channel Reporting Data

Reliable Omni-Channel analytics depend on using the right data source for the right question. AgentWork should be treated as the source of record for assignment timing, while UserServicePresence should be treated as the source of record for presence-duration utilization. Separating those concerns prevents false conclusions, especially when transferred and abandoned work create additional AgentWork records and would otherwise distort totals.

Scalability improves when the reporting model stays channel specific instead of forcing all work into one generic historical join. The researched guidance requires separate Custom Report Types by channel, which keeps each reporting path aligned with its real related object and avoids brittle designs that mix unrelated work-item contexts.

Operational excellence comes from publishing metric definitions alongside the report. Supervisors need to know whether a number represents assignment count, wait time, active time, or presence duration, and they need a clear rule for how transfers and abandons are counted. That documentation is what keeps historical reports consistent with the live mental model operators get from Omni Supervisor.

## Official Sources Used

- [AgentWork Object Reference](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_agentwork.htm) — documents the AgentWork fields used for assignment-level timing and capacity analysis, including RequestDateTime, AcceptDateTime, CloseDateTime, WaitTime, HandleTime, ActiveTime, CapacityWeight, and DeclineReason.
- [UserServicePresence Object Reference](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userservicepresence.htm) — documents the object used to analyze agent presence-status durations for capacity utilization.
- [Omni Supervisor PDF](https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/omnichannel_supervisor.pdf) — explains the live queue, agent, wait-time, and capacity views that inform how supervisors interpret Omni-Channel reporting.
