# LLM Anti-Patterns — Einstein Activity Capture API

Common mistakes AI coding assistants make when generating or advising on Einstein Activity Capture data access from Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Querying Task or EmailMessage for EAC-Synced Activities

**What the LLM generates:**
```apex
List<Task> eacEmails = [
    SELECT Id, Subject, ActivityDate, WhoId
    FROM Task
    WHERE ActivitySource = 'EAC'
    ORDER BY ActivityDate DESC
];
```
or:
```apex
List<EmailMessage> synced = [
    SELECT Id, Subject, FromAddress
    FROM EmailMessage
    WHERE MessageDate >= :cutoff
];
```

**Why it happens:** LLMs are trained on patterns where standard Salesforce activities live in `Task`, `Event`, or `EmailMessage`. EAC is a newer, atypical storage architecture — the training signal for "query EAC emails" matches the general pattern for querying email records.

**Correct pattern:** depends on the org's architecture, which the model must ask about rather than assume.
```apex
// Sync Email as Salesforce Activity: captured email IS standard Task / EmailMessage.
// The Task query above is right here — what was wrong is the invented ActivitySource='EAC' filter.
List<Task> capturedEmails = [
    SELECT Id, Subject, ActivityDate, WhoId
    FROM Task
    WHERE WhoId IN :contactIds AND ActivityDate >= :cutoff
];

// Legacy EAC only: ActivityMetric is the aggregate surface --- and is itself retiring
// in Spring '27, so flag every new use as migration debt rather than a solution.
List<ActivityMetric> metrics = [
    SELECT WhoId, ActivityDate, EmailCount, EmailOpenCount, MeetingCount
    FROM ActivityMetric
    WHERE WhoId IN :contactIds
      AND ActivityDate >= :cutoff
];
```

**Detection hint:** Any query against `Task`, `Event`, or `EmailMessage` presented as a way to "read EAC data" without first establishing the storage architecture — and equally, any answer that reaches for `ActivityMetric` without naming the retirement. Also flag the invented `ActivitySource = 'EAC'` filter, which is the giveaway that the model is pattern-matching rather than reading schema.

---

## Anti-Pattern 2: Assuming EAC Triggers Can Fire on Synced Activity

**What the LLM generates:**
```apex
trigger EacEmailTrigger on Task (after insert) {
    for (Task t : Trigger.new) {
        if (t.ActivitySource == 'EAC') {
            // update last activity date on Contact
        }
    }
}
```

**Why it happens:** LLMs know that Apex triggers fire on standard object DML and that EAC syncs "activities." The logical inference is that syncing an email creates a Task record and therefore fires a trigger. The inference is wrong on **legacy** EAC, which does not write to `Task` at all — and right on Sync Email as Salesforce Activity, where captured email is a standard Task. Stating either unconditionally is the defect.

**Correct pattern:**
```apex
// LEGACY EAC ONLY: no event-driven path exists, so poll on a schedule.
global class UpdateLastEacActivityBatch implements Schedulable {
    global void execute(SchedulableContext sc) {
        // Query ActivityMetric for recent activity and update Contact fields
    }
}
// SYNC EMAIL AS SALESFORCE ACTIVITY: captured email is a real record, so a normal
// Task / EmailMessage trigger fires. The scheduled job above becomes dead weight.
// Declaration vs outcome — not two independent axes.
// DECLARATION is fixed: the trigger always runs implicitly WITHOUT SHARING and
// cannot declare otherwise, so Trigger.new can carry captured email the running
// user cannot otherwise see.
// OUTCOME is per operation: SOQL, SOSL, DML and Database methods in the trigger
// body run in USER mode unless system mode is explicitly specified (apiVersion
// 67.0+ in .trigger-meta.xml, not the org release). User mode enforces sharing,
// FLS, and object permissions and OVERRIDES the trigger's without-sharing
// context for that statement. WITH SYSTEM_MODE / AccessLevel.SYSTEM_MODE opts
// out: FLS and object permissions are skipped, and record sharing falls back
// to the trigger's without-sharing context.
// Set the access mode explicitly in the trigger and its handler. See
// agents/_shared/AGENT_CONTRACT.md "Apex security idiom by API version".
```

Both halves are wrong to state unconditionally. The failure this entry now guards against is a model that has learned the "EAC never fires triggers" rule and repeats it to an org that has already migrated.

**Detection hint:** Any Apex trigger on `Task`, `Event`, or `EmailMessage` that references `ActivitySource == 'EAC'` or tries to filter for EAC-sourced records in `Trigger.new`.

---

## Anti-Pattern 3: DML Against ActivityMetric in Production Code

**What the LLM generates:**
```apex
// Seeding test data
ActivityMetric testMetric = new ActivityMetric();
testMetric.WhoId = contactId;
testMetric.EmailCount = 5;
insert testMetric; // throws DmlException in production context
```

**Why it happens:** LLMs apply the standard test data pattern (create object, set fields, insert) uniformly to all SObjects. They do not know that `ActivityMetric` is a read-only managed object outside of test contexts.

**Correct pattern:**
```apex
// ActivityMetric supports insert ONLY in @isTest contexts
// In production code, never attempt DML on ActivityMetric
// In test classes:
@isTest
static void testEngagementScore() {
    Contact c = new Contact(LastName = 'Test');
    insert c;
    // ActivityMetric can be inserted in @isTest context for mocking
    ActivityMetric m = new ActivityMetric(
        WhoId = c.Id,
        ActivityDate = Date.today(),
        EmailCount = 3,
        MeetingCount = 1
    );
    insert m; // valid only in test context
    // ... assert logic
}
```

**Detection hint:** Any `insert`, `update`, or `delete` against `ActivityMetric` outside of a `@isTest` annotated method or test class.

---

## Anti-Pattern 4: Treating Empty ActivityMetric Results as a Query Error

**What the LLM generates:**
```apex
List<ActivityMetric> metrics = [SELECT ... FROM ActivityMetric WHERE WhoId = :contactId];
if (metrics.isEmpty()) {
    throw new AuraHandledException('EAC data not found — check permissions');
}
```

**Why it happens:** LLMs pattern-match "empty query result" to "permission or configuration error" for most Salesforce objects. For EAC, an empty result is normal and expected for any contact whose record owner has not connected a Gmail or Outlook account.

**Correct pattern:**
```apex
List<ActivityMetric> metrics = [SELECT ... FROM ActivityMetric WHERE WhoId = :contactId];
// Empty results are valid — the contact owner may not have a connected EAC account
// Return a default/zero structure rather than throwing
if (metrics.isEmpty()) {
    return new EngagementSummary(); // zero-value default
}
```

**Detection hint:** Exception throws or error messages inside an `isEmpty()` check on `ActivityMetric` results, especially messages referencing permissions or configuration.

---

## Anti-Pattern 5: Using Standard Activities Report Type to Report on EAC Data

**What the LLM generates:**
```
Recommendation: Create a report using the 'Activities with Contacts and Leads' report type
and filter by ActivitySource = 'EAC' to see all Einstein Activity Capture emails.
```

**Why it happens:** LLMs know that standard Salesforce activities live in the Activities report type family. They do not know that EAC data requires a separate dedicated report type and that the two families are incompatible for joining.

**Correct pattern:**
```
Establish the architecture first.

Sync Email as Salesforce Activity: "Auto-captured emails are now included in standard
report types and appear as standard Tasks." Use the Activities with Accounts or
Activities with Opportunities report type. The unified activity report the business
wants is now possible in one report.

Legacy EAC: the dedicated Einstein Activity Capture report type is the only surface,
and it cannot be joined to standard Activities. Say so AND say that this layer retires
in Spring '27 (February 2027), so the answer is a migration, not a report build.
```

**Detection hint:** Any recommendation to filter standard Activities reports expecting legacy EAC records to appear; and, now more commonly, any recommendation to *build* on the dedicated EAC report type, the Activities Dashboard, or the `Unified*` objects without naming the retirement date.

---

## Anti-Pattern 6: Assuming EAC Data Is Available in Sandbox

**What the LLM generates:**
```apex
// Test in full sandbox — EAC data copied from production should be available
List<ActivityMetric> metrics = [SELECT ... FROM ActivityMetric WHERE WhoId IN :ids];
System.assert(!metrics.isEmpty(), 'Expected EAC data from production copy');
```

**Why it happens:** LLMs know that full sandboxes copy production data. They do not know that EAC connected account credentials are not portable to sandboxes, so live ActivityMetric sync does not run after the sandbox refresh.

**Correct pattern:**
```apex
// Seed ActivityMetric explicitly in @isTest context
// Never assert non-empty EAC results in sandbox without seeding
@isTest
static void testWithSeededEacData() {
    Contact c = new Contact(LastName = 'EACTest');
    insert c;
    insert new ActivityMetric(WhoId = c.Id, ActivityDate = Date.today(), EmailCount = 2);
    // ... test logic using seeded data
}
```

**Detection hint:** Test methods that query `ActivityMetric` without first inserting seed data, or assertions that expect non-zero results from `ActivityMetric` in a test/sandbox context without seeding.

---

## Anti-Pattern 7: Designing Onto the Retiring Activity Metrics Layer

**What the LLM generates:**
```
Recommendation: use the Activity Metrics fields on Account and Opportunity for the
engagement score, add the Activities Dashboard for trend analysis, and report on
UnifiedTask / UnifiedEmail for the unified activity view.
```

**Why it happens:** These were the documented answers for years, so they dominate the training signal. The model has no way to know the layer is being dismantled, and — worse — nothing in the org contradicts it: the fields still exist on the objects, the SOQL still compiles, the report type still appears in the picker. Every signal an LLM can check says the design is fine.

**Correct pattern:**
```
Activity Metrics, the Activities Dashboard, Recommended Connections and A360 Reports
are "scheduled for retirement in Spring '27 (February 2027)". The A360 report types go
with them, along with UnifiedEmail, UnifiedMeeting, UnifiedTask and their participant
objects. Ahead of that, "Activity Metrics fields no longer populate. Custom code or
reports referencing these fields return null values."

Build instead on standard Activity records: "Recreate your activity reporting on Task
and EmailMessage objects grouped by Account or Opportunity," reported through
Activities with Accounts / Activities with Opportunities. For a score that must be
filterable or queryable, "use flows or scheduled jobs to compute and persist
engagement scores into custom fields."
```

**Detection hint:** Any recommendation naming Activity Metrics fields, the Activities Dashboard, Recommended Connections, or a `Unified*` object as a *forward-looking* design, with no retirement date attached. The tell is confident, unqualified present tense about a feature with a published end date — flag the absence of the caveat, not the mention itself, since describing these in a legacy-org context is legitimate.
