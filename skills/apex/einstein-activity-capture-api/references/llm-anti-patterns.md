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

**Correct pattern:**
```apex
// Use ActivityMetric for aggregate EAC data in standard orgs
List<ActivityMetric> metrics = [
    SELECT WhoId, ActivityDate, EmailCount, EmailOpenCount, MeetingCount
    FROM ActivityMetric
    WHERE WhoId IN :contactIds
      AND ActivityDate >= :cutoff
];
```

**Detection hint:** Any query against `Task`, `Event`, or `EmailMessage` presented as a way to "read EAC data" without first confirming Write-Back is enabled. Flag code where a comment says "EAC emails" but the object is Task or EmailMessage.

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

**Why it happens:** LLMs know that Apex triggers fire on standard object DML and that EAC syncs "activities." The logical inference is that syncing an email creates a Task record and therefore fires a trigger. This inference is wrong — EAC sync in standard (non-Write-Back) orgs does not write to `Task` at all.

**Correct pattern:**
```apex
// Use a scheduled Apex job or scheduled flow that queries ActivityMetric
// to detect new activity and update related fields.
// There is no event-driven trigger path for standard EAC sync.
global class UpdateLastEacActivityBatch implements Schedulable {
    global void execute(SchedulableContext sc) {
        // Query ActivityMetric for recent activity and update Contact fields
    }
}
```

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
To report on EAC-synced activities, use the dedicated Einstein Activity Capture report type
available in the Reports tab under the Einstein Activity Capture category.
Standard Activities report types do NOT include EAC-synced records.
Build separate reports for EAC metrics and standard logged activities,
then surface both in a combined dashboard.
```

**Detection hint:** Any recommendation to filter standard Activities reports expecting EAC records to appear, or advice to join EAC report types with standard Activities report types in a single report.

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
