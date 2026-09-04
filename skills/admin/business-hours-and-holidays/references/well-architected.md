# Well-Architected Notes — Business Hours and Holidays

## Relevant Pillars

- **Reliability** — an SLA promise is only as reliable as the calendar behind it. The default 24/7 calendar, an unattached holiday, or an escalation entry on the wrong source each turns a contractual "one business day" into wall-clock time with no error anywhere. Reliability here means every consumer reads a calendar someone chose on purpose.
- **Operational Excellence** — calendars change every year (holidays) and every reorganisation (regions). Keeping them in `Settings:BusinessHours` under source control, with a checker that flags unattached holidays, makes the yearly update a reviewed deploy instead of a Setup click nobody records.

## Architectural Tradeoffs

**One calendar vs one per region:** one calendar is simple and wrong for any org with more than one time zone or holiday set. One per region is correct but only works if something populates `Case.BusinessHoursId` at creation and every escalation entry uses the `Case` source. Choose per-region calendars the moment a second region exists, and treat the Case-calendar Flow as part of the intake design.

**Case calendar vs process calendar as authority:** escalation rules can follow the Case; entitlement milestones follow the process unless overridden. Pick one authority per SLA policy and align the other to it, otherwise the same Case escalates on one clock and misses its milestone on another.

**Apex vs declarative for working-time math:** formulas cannot call `BusinessHours`, and Flow has no business-time element. Any "hours open" number needs Apex (`diff`) or a scheduled job writing a field. Keep that code small and single-purpose; the calendar logic itself stays declarative.

## Anti-Patterns

1. **Leaving the shipped default as the default** — the org "has business hours" but every consumer still counts round the clock.
2. **Holidays created but not attached** — the holiday list looks complete in Setup and pauses nothing.
3. **Setting `Case.BusinessHoursId` after the fact** — a scheduled or after-save update lands after escalation timers were already computed on the default calendar.

## Official Sources Used

- Metadata API Developer Guide: BusinessHoursSettings (fields, `HH:mm:ss.SSSZ` format, holiday `businessHours` attachment, sample definition) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_businesshourssettings.htm
- Metadata API Developer Guide (PDF, v62) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide: EscalationRules (`businessHoursSource` values `None` / `Case` / `Static`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_escalationrules.htm
- Object Reference: BusinessHours ("Escalation rules are run only during these hours"; holidays suspend business hours and the escalation rules using them; readable by all users via the API; list views capped at 10,000) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_businesshours.htm
- Object Reference (PDF, v62) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Reference Guide: BusinessHours Class (`add`, `addGmt`, `diff`, `isWithin`, `nextStartDate`) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_BusinessHours.htm
- Apex Developer Guide (PDF, v62; BusinessHours usage example with `60 * 60 * 1000L`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Help: Set Business Hours — https://help.salesforce.com/s/articleView?id=sf.customize_supporthours.htm
- Salesforce Help: Set Up Case Escalation Rules — https://help.salesforce.com/s/articleView?id=sf.customize_escalation.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
