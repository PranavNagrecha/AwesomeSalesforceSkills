# Well-Architected Notes — Entitlements and Milestones

## Relevant Pillars

- **Reliability** — Entitlement processes are the authoritative mechanism for enforcing SLA commitments on cases. A reliable implementation ensures that every case created through every intake channel (Email-to-Case, Web-to-Case, API, UI) has an entitlement applied, milestone timers are running, and violation actions fire without gaps. Reliability failures here are typically silent: no errors are thrown when entitlements are absent, so manual validation is required.
- **Easy (User and Admin Experience)** — Milestone Tracker components on the Case record give agents real-time visibility into remaining SLA time. Surfacing this clearly reduces cognitive overhead and allows agents to self-prioritize without relying on manager intervention. Overly complex multi-tier process configurations with too many milestones per process increase maintenance burden without proportional benefit.
- **Adaptable** — Entitlement process versioning supports evolving SLA commitments without disrupting in-flight cases. Designing processes as one-per-tier (rather than attempting to handle all tiers in one process) makes it easier to modify a single tier's SLAs as contracts change. Using Record-Triggered Flows for entitlement creation (rather than manual creation) means the automation adapts to new product lines without admin rework.
- **Security** — Milestone action email alerts reference case data. Ensure that email alert templates do not expose sensitive case fields to recipients outside the intended audience. Violation alerts sent to VP-level distribution lists or external customer success platforms should be reviewed for field-level security implications.

## Architectural Tradeoffs

**Business hours at the process level vs. milestone level:**
Assigning business hours at the process level is simpler to maintain — one change updates all milestones in the process. However, if different milestones within the same process need different coverage windows (e.g., a first-response milestone is 24/7 but a resolution milestone is business-hours only), milestone-level override is required. Over-using milestone-level overrides increases configuration complexity and makes auditing harder. Prefer process-level assignment unless there is a documented business requirement for per-milestone windows.

**Entitlement templates + Flow vs. manual entitlement creation:**
Manual entitlement creation is viable for small customer bases or for enterprise accounts managed by dedicated CSMs. It becomes error-prone at scale. Automation via Flow ensures consistent entitlement assignment but introduces a dependency on the Flow's activation state. If the Flow is deactivated for maintenance, new entitlements are not created. Implement monitoring (e.g., a scheduled report counting cases with no entitlement created in the last 24 hours) to detect Flow outages.

**No Recurrence vs. Independent recurrence for response milestones:**
No Recurrence is safer for most SLA tracking use cases. Independent recurrence provides more accurate tracking for multi-touch interactions but introduces the risk of action storms and stacking. Choose Independent recurrence only when each recurrence represents a genuinely distinct contractual commitment, and always pair it with action suppression conditions.

## Anti-Patterns

1. **Hardcoding SLA deadlines in Flow or Apex instead of using entitlement processes** — Building a Flow that calculates `Case.CreatedDate + 4 hours` and stores the result as the SLA deadline bypasses all of the native milestone infrastructure (business hours pausing, action timers, Milestone Tracker UI component, version management). It creates a parallel SLA tracking system that diverges from the entitlement model and cannot be maintained by configuration alone. Use entitlement processes for SLA tracking; use Flow only for entitlement creation automation.

2. **One monolithic entitlement process for all tiers** — Using conditional logic (e.g., a milestone with different time limits per a case field value) within a single entitlement process makes versioning and maintenance dangerous. Changes to one tier's milestones affect all tiers. Design one process per support tier so each tier can be versioned and modified independently.

3. **Relying on Classic entitlement template product attachment in a Lightning org** — As of Lightning Experience, the product attachment UI does not exist. Orgs that migrate from Classic to Lightning without building a replacement Flow lose automated entitlement creation entirely. This is frequently discovered months after migration when a support report shows that recent customers have no SLA tracking. Always build and test the Flow replacement before disabling Classic.

## Official Sources Used

Primary sources, with the claim each one carries. Line numbers are `grep -n` offsets into the plain-text
extracts of the Summer '26 / v62 PDFs.

- **Metadata API Developer Guide — `EntitlementProcess`, `EntitlementProcessMilestoneItem`,
  `EntitlementProcessMilestoneTimeTrigger`** (api_meta.txt:59069–59308) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — the deployable shape in
  `references/metadata-examples.md` § 2, the version-derived file name, and the fact that milestone
  thresholds are signed `timeLength` offsets rather than percentages (gotcha 6).
- **Metadata API Developer Guide — `MilestoneType`** (api_meta.txt:88319–88380) — the three
  `recurrenceType` values `none` / `recursIndependently` / `recursChained`, the guide's own mapping of
  `recursChained` to "sequential recurrence", and the fact that recurrence is a property of the
  milestone type rather than of the process that uses it (gotcha 7).
- **Metadata API Developer Guide — `EntitlementTemplate` and `EntitlementSettings`**
  (api_meta.txt:59310–59374, 115601–115730) — the template's `businessHours` / `term` /
  `casesPerEntitlement` semantics, and `enableEntitlements`, `enableEntitlementVersioning`,
  `enableMilestoneStoppedTime`, `ignoreMilestoneBusinessHours` (gotchas 10 and 12, and the
  "Architectural Tradeoffs" note on templates versus manual creation).
- **Metadata API Developer Guide — `Workflow`, `WorkflowActionReference`, `WorkflowAlert`,
  `WorkflowFieldUpdate`** (api_meta.txt:139874–140195) — the container the milestone actions are
  deployed in, the five valid action `type` values, the required fields on each action, and the
  `reevaluateOnChange` cascade limit behind the "keep SLA stamps inert" recommendation.
- **Object Reference — `SlaProcess`** (object_reference.txt:270637–270790) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf — the absence of
  `create()` and `update()` on the process record, the auto-generated `NameNorm`, the `Case` /
  `Work Order` split on `SObjectType`, and the versioning fields' dependence on the versioning switch
  (gotcha 12, and the "Adaptable" pillar note on versioning).
- **Object Reference — `CaseMilestone`** (object_reference.txt:63342–63470) — no `create()` or
  `delete()`, and `CompletionDate` / `StartDate` as the only updateable fields, which is why a milestone
  never completes on its own (gotcha 8) and why the Apex in `references/metadata-examples.md` § 9 is an
  update rather than an insert.
- **Object Reference — `Entitlement`, `EntitlementContact`, and the `Case` entitlement fields**
  (object_reference.txt:110176–110480, 62245–62700) — `BusinessHoursId` documented Required but not
  createable or updateable, `Status` derived from `StartDate` / `EndDate`, `RemainingCases` decrementing
  per case, and `Case.IsStopped` / `Case.StopStartDate` / `Case.SlaStartDate` (gotchas 9, 10 and 11).
- **Apex Developer Guide — debug log event table** (apexdev.txt:39104–39117) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf —
  the `SLA_PROCESS_CASE`, `SLA_EVAL_MILESTONE`, `SLA_NULL_START_DATE` and `SLA_END` events under the
  Workflow category, which is the diagnosis path in `references/examples.md` and
  `references/metadata-examples.md` § 9.
- **Salesforce App Limits Cheat Sheet** (salesforce_app_limits_cheatsheet.txt) — checked and reported as
  a negative result: `grep -i "entitlement\|milestone"` returns one unrelated row about the API Request
  Limit usage-based entitlement. **No milestones-per-process or processes-per-org limit is published
  there**, which is why the "up to 10 milestones per process" figure in `SKILL.md` is marked UNVERIFIED
  rather than restated as fact.
- **Salesforce Well-Architected — Reliable** —
  https://architect.salesforce.com/docs/architect/well-architected/reliable/overview.html — the framing
  for "reliability failures here are silent" in the Relevant Pillars section above.
- **Salesforce Well-Architected — overview** —
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — pillar naming.
- Salesforce Help topics used for orientation only, and **not** relied on for any behaviour claim above
  (help.salesforce.com cannot be fetched for verification):
  `sf.entitlements_overview.htm`, `sf.entitlements_milestones_actions.htm`,
  `sf.entitlements_business_hours.htm`, `sf.entitlements_templates_overview.htm`.
