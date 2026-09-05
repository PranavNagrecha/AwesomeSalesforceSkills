# Well-Architected Mapping: Flow for Admins

---

## Pillars Addressed

### Scalability

**Principle: Automation That Works at Real Data Volumes**
Flows that work for one record often fail at 200. Governor limits aren't theoretical — they define the outer bound of what's possible. Every Record-Triggered Flow must be designed to handle bulk operations without hitting those limits.

- WAF check: Does the flow avoid SOQL inside loops?
- WAF check: Does the flow use collection variables and single DML operations instead of per-record DML?
- WAF check: Is the flow tested with 200+ records before production deployment?

**How this skill addresses it:**
- Bulkification rules are explicit and non-optional
- The Get Records pattern (outside loop, filter inside) is the standard approach
- Mode 2 (Review) flags SOQL-in-a-loop as Critical

**Risk of not following this:** Flow works in sandbox (low data volume), fails in production during peak load or data migrations. Silent failures due to unhandled exceptions. Users lose work.

### Reliability

**Principle: Failures Are Visible and Recoverable**
A Flow that fails without a fault connector rolls back the transaction, shows the user a generic error, and notifies no one in a useful way. This is a reliability failure — the system broke and left no trace.

- WAF check: Do all DML and callout elements have fault connectors?
- WAF check: Does the fault path notify someone who can act on it?
- WAF check: Are errors logged in a queryable way (not just email notifications)?

**How this skill addresses it:**
- Fault connector requirement is explicitly non-negotiable
- Fault path patterns are documented (email minimum, custom object logging preferred)
- Mode 3 (Debug) provides systematic approach to finding and fixing failures

**Risk of not following this:** Silent failures. Data corruption (partial updates with no rollback). Users unable to save records with no explanation. Admins unaware of systemic issues.

### Operational Excellence

**Principle: Maintainable Automations**
A Flow with 15 decision elements, variables named `variable1` through `variable15`, and 12 active old versions is not maintainable. The next admin to open it won't understand it. It can't be safely modified.

- WAF check: Are variables named descriptively?
- WAF check: Is reusable logic extracted into Subflows?
- WAF check: Are old Flow versions deactivated?

**How this skill addresses it:**
- Naming standards enforced in Mode 2 review
- Subflow refactor trigger fires when complexity exceeds threshold
- Version management covered in Proactive Triggers

**Risk of not following this:** Flow becomes a black box. Changes break unexpected things. No one knows what the Flow does or why. Debugging takes days instead of hours.

---

## Pillars Not Addressed

- **Security** — Flows run in the sharing context of the user who triggered them (user-context) unless explicitly set to run in system context. Record access is governed by the sharing model. This skill doesn't cover the security implications of running flows in system context — see `flow/flow-runtime-context-and-sharing` and `security/record-access-troubleshooting`.
- **User Experience** — Screen Flow UX design (layout, help text, progress indicators) is out of scope for this skill. Focus here is on correct logic and fault handling.
- **Performance** — Flow performance is mostly a function of bulkification (covered) and SOQL efficiency (covered). Deep performance profiling of Flows is not in scope.

---

## Automation Layer Decision Guide

Use this to decide whether Flow is the right tool:

| Scenario | Recommended Tool | Reason |
|----------|-----------------|--------|
| Simple field update on save | Before-Save Flow | Fastest, no DML overhead |
| Create related record on save | After-Save Flow | DML allowed, Admin-maintainable |
| Complex cross-object logic, bulk | Apex Trigger | More control over SOQL patterns |
| User-guided process | Screen Flow | Declarative, no code |
| Scheduled batch operation (>~50K records per run) | Batch Apex | Repo routing line, `flow-pattern-selector.md` Q6; the platform ceiling underneath it is org-wide interviews per 24 h, not per run |
| Real-time integration callout | Platform Event + Apex | More robust error handling |
| Admin-configurable logic called from Apex | Autolaunched Flow | Separates config from code |

## Official Sources Used

- Metadata API Developer Guide — *Flow* metadata type: the `processType`, `status`, `apiVersion`, and `triggerOrder` fields, the `start` element's `triggerType` / `recordTriggerType` / `filterFormula` / `filters` / `doesRequireRecordChangedToMeetCriteria`, and the Metadata API limitations list (deploy-to-active in non-production only; version deletion blocked by paused interviews; managed-package flows unreachable unless templates). Supports the Reliability and Operational Excellence sections and the deployability material in `references/metadata-examples.md`. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *FlowSettings* → `enableFlowDeployAsActiveEnabled`: "When the value is `false`, all processes and flows are deployed as inactive… The default value is `false` for production orgs and is `true` for non-production orgs." Supports the Operational Excellence claim that sandbox success is not evidence about production. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *FlowDefinition* and *Upgrade Flow Files to API Version 44.0 or Later*: the recommendation to stop using `FlowDefinition` for activation, and the rule that a deployed flow definition's `activeVersionNumber` overrides the `status` field in the flow. Supports the activation guidance and the "deploy landed but the wrong version is running" failure mode. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — *FlowTest*: `.flowtest` suffix, `flowtests` folder, API version 55.0+, and the `testType` value `WithAssertion`. Supports the Operational Excellence position that flow tests are deployable metadata but are not Apex coverage. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide — *Triggers and Order of Execution*: before-save flows at step 3, validation rules at step 5, duplicate rules at step 6, workflow field updates at step 11 (triggers re-fire, "custom validation rules, flows, duplicate rules… aren't run again"), after-save flows at step 14, and asynchronous flow paths in post-commit logic at step 20. Supports the Reliability section and three gotchas about cross-automation interference. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Object Reference — *FlowDefinitionView* and *FlowVersionView*: the verification fields (`ActiveVersionId`, `LatestVersionId`, `IsActive`, `IsOutOfDate`, `ProcessType`, `TriggerType`, `RecordTriggerType`, `TriggerOrder`, `VersionNumber`, `Status`) and the `FlowVersionView` usage constraint that a query must be filtered by `DurableId` or `FlowDefinitionViewId`. Supports the post-deploy verification step and the version-hygiene guidance. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce Developer Limits and Allocations Quick Reference — Per-Transaction Apex Limits: 100/200 SOQL, 150 DML statements, 10,000 DML rows, 50,000 rows queried, 10,000 ms CPU, 6 MB heap, 100 callouts / 120 s cumulative timeout. Supports the Scalability section and the bulkification arithmetic in SKILL.md. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- Salesforce Well-Architected — reliability and operability framing for automation choices, used for the pillar structure of this file.
- Repo decision trees: `standards/decision-trees/automation-selection.md` (Q2–Q6, Q10) and `standards/decision-trees/flow-pattern-selector.md` (Q1–Q9, § Transaction boundary summary). The routing table in SKILL.md cites these by step; the ~50k-per-run escalation line and the "After-Save is inline, not a new transaction" correction both come from them.
