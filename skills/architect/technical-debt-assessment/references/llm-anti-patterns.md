# LLM Anti-Patterns — Technical Debt Assessment

Common mistakes AI coding assistants make when generating or advising on Salesforce technical debt assessments.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Flagging All Apex Triggers as Technical Debt

**What the LLM generates:** "This org has 47 Apex triggers — this is significant technical debt that should be migrated to Flows" without evaluating whether the triggers are well-structured, follow a trigger framework pattern, and handle logic that genuinely requires Apex (callouts, complex error handling, bulkified operations).

**Why it happens:** LLMs conflate "Apex trigger" with "legacy code" because much of the training data discusses migrating triggers to Flows. Well-designed Apex triggers using a handler pattern (e.g., TriggerHandler, fflib) are not technical debt — they are a valid and often preferable architecture.

**Correct pattern:**

```text
Apex triggers are technical debt ONLY when:
1. They lack a handler pattern (logic directly in the trigger body)
2. They are not bulkified (SOQL or DML inside loops)
3. They duplicate logic also present in Flows or Process Builders on the same object
4. They reference deprecated APIs or hard-coded IDs
5. They have no test coverage or tests with assert-free "coverage only" patterns

Well-structured triggers using a framework (fflib, TriggerHandler) with
proper test coverage are NOT technical debt. Do not recommend migration
to Flow unless the team explicitly wants to reduce Apex footprint.
```

**Detection hint:** Flag technical debt reports that recommend "migrate all triggers to Flow" without evaluating trigger quality. Check whether the recommendation includes a per-trigger assessment.

---

## Anti-Pattern 2: Ignoring Process Builder and Workflow Rule Migration Priority

**What the LLM generates:** Technical debt assessments that focus on Apex code quality and custom object proliferation but do not flag active Process Builders and Workflow Rules as high-priority debt, even though Salesforce has officially retired Process Builder for new creation and is phasing out Workflow Rules.

**Why it happens:** Process Builders and Workflow Rules still "work" in production, so LLMs do not flag them as urgently as deprecated APIs. Training data does not consistently reflect Salesforce's retirement roadmap for these tools.

**Correct pattern:**

```text
Technical debt priority for legacy automation:

HIGH priority:
- Active Process Builders: retired for new creation Spring '23, will eventually
  be fully retired. Use the Migrate to Flow tool.
- Workflow Rules with field updates or email alerts: replace with
  record-triggered Flows.

MEDIUM priority:
- Workflow Rules with time-based triggers: test carefully during migration,
  as Flow scheduled paths have different execution characteristics.
- Process Builders that call Apex invocable actions: migration path is
  straightforward but requires testing the Apex interface.

Query active legacy automation:
  SELECT Id, Name, TableEnumOrId FROM FlowDefinitionView
  WHERE ProcessType = 'Workflow' AND IsActive = true
```

**Detection hint:** Flag technical debt reports that do not mention Process Builder or Workflow Rule counts. Check for `ProcessType = 'Workflow'` or `ProcessType = 'InvocableProcess'` in the assessment scope.

---

## Anti-Pattern 3: Treating All Unused Apex Classes as Dead Code That Should Be Deleted

**What the LLM generates:** "These 30 Apex classes have not been modified in 2 years and have no test class references — they should be deleted as dead code" without checking whether the classes are invoked by Flows, referenced by Custom Metadata, called via Schedulable/Batchable interfaces, or used by managed packages.

**Why it happens:** LLMs apply generic dead code detection heuristics (no recent modifications, no direct references) without understanding Salesforce's dynamic invocation patterns. Apex classes can be invoked by metadata configuration (Flow, Process Builder, Schedulable, Batch) that does not appear in static code analysis.

**Correct pattern:**

```text
Before marking Apex as dead code, check ALL invocation paths:
1. Trigger handlers: referenced by trigger files
2. Schedulable: CronTrigger records for scheduled jobs
3. Batch Apex: called by Schedulable classes or other Batch finish() methods
4. Flow invocable: InvocableMethod annotation, referenced by Flow metadata
5. REST/SOAP web services: @RestResource or WebService annotations called externally
6. Visualforce controllers: referenced by Visualforce pages
7. Aura/LWC controllers: @AuraEnabled methods called by components
8. Managed package references: called by installed packages
9. Custom Metadata or Custom Settings: class names stored as configuration

Query: SELECT ApexClassId, CronExpression FROM CronTrigger WHERE CronJobDetail.JobType = '7'
to find scheduled Apex that may reference "unused" classes.
```

**Detection hint:** Flag dead code recommendations that rely solely on "last modified date" or "no direct class reference." Check for Schedulable, InvocableMethod, @RestResource, and @AuraEnabled annotations before deleting.

---

## Anti-Pattern 4: Missing Automation Overlap as a Key Debt Category

**What the LLM generates:** Technical debt assessments that evaluate code quality and data model complexity but do not check for overlapping automation on the same object — multiple triggers, Flows, Process Builders, and Workflow Rules all firing on the same event and potentially conflicting.

**Why it happens:** Automation overlap is an emergent problem from years of incremental development. LLMs assess each automation artifact individually rather than mapping the full execution chain on an object-by-object basis.

**Correct pattern:**

```text
Automation overlap assessment per object:

For each object with automation:
1. Count active record-triggered Flows (before-save and after-save)
2. Count active Apex triggers (before and after)
3. Count active Process Builders (should be zero for new design)
4. Count active Workflow Rules (should be zero for new design)
5. Map validation rules that interact with automated field updates

Flag any object that has:
- Both an Apex after-trigger AND an after-save Flow (potential recursion)
- A Process Builder AND a record-triggered Flow (overlapping execution)
- More than 3 distinct automation entry points (maintenance complexity)

Query: SELECT TableEnumOrId, COUNT(Id) FROM FlowDefinitionView
WHERE IsActive = true AND ProcessType IN ('AutoLaunchedFlow','Workflow','InvocableProcess')
GROUP BY TableEnumOrId HAVING COUNT(Id) > 2
```

**Detection hint:** Flag technical debt assessments that do not include an object-level automation inventory. Look for missing "automation per object" analysis.

---

## Anti-Pattern 5: Recommending Wholesale Migration Instead of Incremental Remediation

**What the LLM generates:** "You should re-architect the entire org" or "Migrate all automation to a new framework" as a single big-bang project, without assessing risk, estimating effort per item, or proposing an incremental remediation plan prioritized by business impact.

**Why it happens:** LLMs provide idealized recommendations without operational constraints. A "clean slate" approach sounds technically correct but ignores the reality that production orgs cannot be paused for months of rework.

**Correct pattern:**

```text
Technical debt remediation should be incremental and prioritized:

Priority 1 (address immediately):
- Security vulnerabilities (missing CRUD/FLS, SOQL injection)
- Deprecated API versions that will break on next release
- Automation causing production errors or data corruption

Priority 2 (address in next 2 quarters):
- Process Builder and Workflow Rule migration to Flow
- Hard-coded IDs that block sandbox refresh
- Unused permission sets with over-provisioned access

Priority 3 (plan for next major project):
- Trigger framework adoption (if triggers lack a handler pattern)
- Data model normalization (junction objects, polymorphic lookups)
- Test class quality improvement (add meaningful assertions)

Each remediation item should have: effort estimate, risk rating,
business impact, and a rollback plan.
```

**Detection hint:** Flag technical debt recommendations that propose "rewrite everything" without a phased plan or priority rating. Check for missing effort estimates and risk assessments per remediation item.
