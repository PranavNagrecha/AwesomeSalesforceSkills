# Well-Architected Notes: Omni-Channel Reporting Data

Reliable Omni-Channel analytics depend on using the right data source for the right question. AgentWork should be treated as the source of record for assignment timing, while UserServicePresence should be treated as the source of record for presence-duration utilization. Separating those concerns prevents false conclusions, especially when transferred and abandoned work create additional AgentWork records and would otherwise distort totals.

Scalability improves when the reporting model stays channel specific instead of forcing all work into one generic historical join. `AgentWork.WorkItemId` is polymorphic, so each channel's business fields live on a different object; filtering by channel keeps each reporting path aligned with its real related object.

Operational excellence comes from publishing metric definitions alongside the report. Supervisors need to know whether a number represents assignment count, speed to answer, handle time, active time, or presence duration, and they need a clear rule for how transfers and abandons are counted. That documentation is what keeps historical reports consistent with the live mental model operators get from Omni Supervisor.

## Official Sources Used

Read for this revision (2026-10-03):

- Salesforce Object Reference, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. AgentWork (all fields, Status values, IsTransfer and IsConference API note, ActiveTime and CapacityModel, OriginalGroupId, PendingServiceRoutingId, usage); UserServicePresence (StatusDuration and StatusEndDate set at status end, IsCurrentState, no Apex triggers); PendingServiceRouting (description, GroupId versus QueueId, Limits); ServiceChannel (RelatedEntity); LiveChatTranscript (WaitTime).
- SOQL and SOSL Reference, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_soql_sosl.pdf. "Using the Type Qualifier" for polymorphic fields; COUNT_DISTINCT(); date literals.
- Omni Supervisor, Spring '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/omnichannel_supervisor.pdf. Real-time tabs, Agent Detail field definitions (Handle Time as now minus accept), Offline stops tracking, Agent Timeline shows AgentWork status.
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. ReportType (baseObject, category values, sections, ReportTypeColumn, lookup notation in the sample).

Listed in the original version and not re-read:

- AgentWork Object Reference (atlas page): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_agentwork.htm (same content read in the PDF above).
- UserServicePresence Object Reference (atlas page): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userservicepresence.htm (same content read in the PDF above).
