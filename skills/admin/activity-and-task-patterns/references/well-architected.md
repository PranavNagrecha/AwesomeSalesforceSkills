# Well-Architected Notes — Activity and Task Patterns

## Relevant Pillars

The Activity model touches three Well-Architected pillars in different
weights. Practitioners who only weigh one of them tend to ship a design
that breaks on the other two.

- **Reliability** — The Activity model has hard platform constraints
  (500-row `ActivityHistory` subquery cap, polymorphic `WhatId`
  validation, shared FLS between Task and Event) that an unsuspecting
  implementation will hit at scale. Designing for reliability here
  means choosing the right object (Task/Event vs custom
  `Interaction__c`) at the *volume* threshold, not after the limit
  errors start arriving in production.
- **Performance** — Polymorphic SOQL without `TYPEOF` issues O(N)
  hidden subqueries per row when downstream code does
  `task.What.Name` on a typed reference. Bulk task creation done as
  loop-DML rather than collect-and-insert hits the 150-DML governor
  at the 75-record mark. Both patterns are invisible in unit tests
  but obvious in production load.
- **Operational Excellence** — Activity reporting splits across
  three surfaces (`Task`/`Event` direct, `ActivityHistory`/`OpenActivity`
  subqueries, Activity Metrics for EAC) and it is the platform owner's
  job to document which surface is authoritative for which question.
  Without that documentation, every new dashboard re-litigates the
  same source-of-truth decision and produces conflicting numbers.

## Architectural Tradeoffs

The dominant tradeoff is **standard Task/Event vs custom
`Interaction__c`**:

| Dimension | Task/Event | Custom `Interaction__c` |
|---|---|---|
| UI integration | Native Lightning timeline | Build your own LWC |
| Polymorphic parent | Free (`WhatId`) | Build many lookups |
| Sharing | Inherits from `WhatId` parent — no control | Full custom sharing model |
| Custom fields | Propagate to both Task AND Event | Per-object |
| Reporting | First-class report types | Need to define |
| Volume ceiling | ~50k/day per object before performance degradation | Limited by storage, not surface |
| EAC integration | Native | Build connector |

The decision pivots almost entirely on **volume** and **sharing
requirements**. Anything that needs an independent sharing model
(per-rep visibility on interactions across a shared account, for
example) cannot use Task/Event and must use a custom object. Anything
that needs to plug into the standard Lightning timeline without an LWC
build cannot use a custom object and must use Task/Event.

A common mistake is to assume "custom object is always more flexible
so always pick that." It is — and it costs you the Lightning record
page timeline, the standard "log a call" mobile flow, the Outlook /
Gmail integration, and Einstein Activity Capture. For organizations
where reps live in the timeline, those features are worth more than
the custom-sharing flexibility.

## Anti-Patterns

1. **Querying the abstract `Activity` parent.** `Activity` is read-only
   and abstract — only `Task` and `Event` are concrete. Practitioners
   try `SELECT Id FROM Activity` because it shows up in the object
   reference docs alongside its children. Always pick the concrete
   child object or a subquery from an activity-enabled parent.
2. **Treating `WhoId` as a Contact-only lookup.** `WhoId` is polymorphic
   between Contact and Lead, and many Apex implementations cast it to
   `Contact.Id` directly. This corrupts data on insert when the
   underlying record is a Lead.
3. **Sharing rules on Activities.** Activities inherit sharing from
   their `WhatId` parent — *there is no Activity sharing object you
   can write rules against*. Practitioners come from other CRMs where
   activities have their own ACL and try to apply the same pattern.
   If you need activity-level sharing, you need a custom object.

## Official Sources Used

- Object Reference — Activity, Task, Event, ActivityHistory, OpenActivity:
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_activity.htm
- SOQL and SOSL Reference — `TYPEOF` clause:
  https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_typeof.htm
- Einstein Activity Capture Setup Guide:
  https://help.salesforce.com/s/articleView?id=sf.einstein_sales_aac_setup_parent.htm&type=5
- Salesforce Well-Architected — Reliability:
  https://architect.salesforce.com/well-architected/trusted/reliable
- Salesforce Well-Architected — Performance:
  https://architect.salesforce.com/well-architected/adaptable/resilient
