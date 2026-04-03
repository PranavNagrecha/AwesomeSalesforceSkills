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

- **Security** — Flows run in the sharing context of the user who triggered them (user-context) unless explicitly set to run in system context. Record access is governed by the sharing model. This skill doesn't cover the security implications of running flows in system context — see security/fls-crud.
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
| Scheduled batch operation (>10K records) | Batch Apex | Flow has 250K interview limit |
| Real-time integration callout | Platform Event + Apex | More robust error handling |
| Admin-configurable logic called from Apex | Autolaunched Flow | Separates config from code |

## Official Sources Used

- Salesforce Well-Architected Overview — reliability and operability framing for automation choices
- Metadata API Developer Guide — Flow metadata behavior and deployment context
