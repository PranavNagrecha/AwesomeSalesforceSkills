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
  loop-DML rather than collect-and-insert hits the synchronous
  150-statement DML governor (salesforce_app_limits_cheatsheet.txt L64;
  apexdev.txt L19554) on the 151st iteration. Both patterns are invisible in unit tests
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
| Volume ceiling | Not a published number — UNVERIFIED (2026-09-05): the "~50k/day per object" figure quoted in `SKILL.md` is a field heuristic; no activity-volume ceiling appears in the App Limits cheat sheet or the LDV guide. The grounded constraint is the read path: `Subject`, `TaskStatus` and `TaskPriority` are on the platform's can't-index list (ldv.txt L498–L511) | Limited by storage, not by an unindexable filter |
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

Every source below was read for this skill; the parenthetical says which claim it
carries. Line references are `grep -n` positions in the extracted plain text of the
v62 / Summer '26 PDFs.

- **Metadata API Developer Guide — `ActivitiesSettings`**
  (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf,
  api_meta.txt L109357–L109592) — the full org-settings field table, the read-only
  Shared Activities switch behind Gotcha 8, the `Settings`/`Activities` package
  manifest, and the "wildcard doesn't apply to feature settings" rule; source for
  `references/metadata-examples.md` section 1.
- **Metadata API Developer Guide — `CustomObject.enableActivities`, `CustomField`,
  `ValueSet`, `StandardValue`** (api_meta.txt L42009–L42012, L43704–L43711,
  L45839–L45870, L47542–L47592) — which objects can be a `WhatId`, the picklist
  `valueSet` shape for a shared Activity field, and the `closed` / `highPriority`
  flags that derive `Task.IsClosed` and `Task.IsHighPriority`; source for
  `references/metadata-examples.md` sections 2–4.
- **Object Reference — `Task`, `Event`, `TaskRelation`, `EventRelation`,
  `ActivityHistory`, `OpenActivity`, `LookedUpFromActivity`, `EmailMessage`**
  (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf,
  object_reference.txt L277879+, L111415+, L278698+, L130957+, L23502, L191446,
  L177391, L104010) — `WhatId`/`WhoId` polymorphism and their `Refers To` lists;
  `ActivityHistory` and `OpenActivity` supporting `describeSObjects()` only, which
  is why they are projections rather than queryable objects; the Shared Activities
  relationship ceilings (one lead or 50 contacts; 1,000 invitees non-recurring, 100
  recurring); shared Task/Event field-level security in metadata deploys; child-event
  update restrictions; and the EmailMessage-replaces-its-Task behaviour in Gotcha 10.
- **Apex Developer Guide — Working with Polymorphic Relationships in SOQL Queries,
  `Database.DMLOptions.emailHeader`, partial-success DML**
  (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf,
  apexdev.txt L9770–L9787, L8588–L8647, L7566–L7586) — `TYPEOF`, the `What.Type`
  filter form, `instanceof` narrowing, and the `triggerUserEmail` /
  `triggerOtherEmail` behaviour that makes bulk task creation mail every assignee
  (Gotcha 6).
- **Apex Reference Guide — `Database.insert` overloads and `DmlOptions.optAllOrNone`**
  (apexrefguide.txt L207936–L207953, L148087–L148104) — the
  `insert(List<SObject>, Database.DMLOptions, System.AccessLevel)` signature, the
  default-to-user-mode rule, and the partial-success semantics used in
  `references/metadata-examples.md` section 5.
- **Best Practices for Deployments with Large Data Volumes** (ldv.txt L458–L511) —
  the standard/custom index selectivity thresholds and the list of standard fields
  the platform can't index, which includes Activity `Subject`, `TaskStatus` and
  `TaskPriority` (Gotcha 7) and underpins the Task/Event vs `Interaction__c`
  tradeoff table above.
- **SOQL and SOSL Reference — `TYPEOF` clause:**
  https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_typeof.htm
  (the `WHEN … THEN … ELSE … END` grammar quoted in `references/examples.md`).
- **Einstein Activity Capture Setup Guide:**
  https://help.salesforce.com/s/articleView?id=sf.einstein_sales_aac_setup_parent.htm&type=5
  (the EAC store being separate from `Task`/`Event`, behind Gotcha 4). UNVERIFIED
  (2026-09-05): help.salesforce.com cannot be fetched in this environment, and no
  EAC storage or reporting statement appears in the PDF corpus above — treat every
  EAC claim in this skill as needing a check against the live setup guide.
- **Salesforce Well-Architected — Reliability:**
  https://architect.salesforce.com/well-architected/trusted/reliable
  (the "design to the constraint, not to the error message" framing in the
  Reliability bullet).
- **Salesforce Well-Architected — Resilient:**
  https://architect.salesforce.com/well-architected/adaptable/resilient
  (the Performance bullet's "invisible in unit tests, obvious under production load"
  framing).
