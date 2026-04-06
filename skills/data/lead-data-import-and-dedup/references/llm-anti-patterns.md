# LLM Anti-Patterns — Lead Data Import and Dedup

Common mistakes AI coding assistants make when generating or advising on Lead data import and dedup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Advising That Duplicate Rule "Block" Prevents Web-to-Lead Duplicates

**What the LLM generates:** "Enable your Duplicate Rule with action 'Block' to prevent duplicate leads from being created by your web form."

**Why it happens:** LLMs trained on general Salesforce documentation learn that Duplicate Rules with "Block" prevent duplicates — this is true for UI-based entry. The channel-specific exception for Web-to-Lead and API inserts is a less prominent footnote and often omitted from training data.

**Correct pattern:**

```
Web-to-Lead and API inserts bypass Duplicate Rule blocking. Set the rule to "Alert"
to capture DuplicateRecordSets, then implement an after-insert Apex trigger or Flow
to detect and route duplicates for these channels.
```

**Detection hint:** Any answer containing "Block" mode as sufficient for Web-to-Lead or API without mentioning the bypass behavior or recommending a trigger/Flow complement.

---

## Anti-Pattern 2: Claiming Data Import Wizard Uses the Same Fuzzy Matching as Duplicate Rules

**What the LLM generates:** "The Data Import Wizard will use your configured Matching Rules to deduplicate records during import."

**Why it happens:** LLMs conflate the two dedup mechanisms. Duplicate Rules + Matching Rules are one system. Data Import Wizard has its own separate dedup capability that does not use Matching Rules at all. This is a subtle distinction that training data often glosses over.

**Correct pattern:**

```
The Data Import Wizard performs single-field exact-match dedup on one user-chosen
field (Email, Name, or External ID). It does not invoke Matching Rules or Duplicate
Rules. For fuzzy multi-field dedup during imports, pre-normalize the file externally
and choose Email as the wizard match field.
```

**Detection hint:** Any answer that says the wizard "uses your matching rules" or "applies duplicate detection rules" without clarifying that only exact single-field matching is supported.

---

## Anti-Pattern 3: Recommending Database.merge() Inside a Before-Insert or After-Insert Trigger

**What the LLM generates:**

```apex
trigger MergeOnInsert on Lead (after insert) {
    // Merge duplicate with existing lead
    Database.merge(existingLead, Trigger.new[0], false);
}
```

**Why it happens:** LLMs know that `Database.merge()` is the Apex merge mechanism and that triggers are the standard hook for lead insert events. Combining them seems logical, but it causes recursive trigger execution and hits governor limits rapidly.

**Correct pattern:**

```apex
// In after-insert trigger: flag the record, do NOT merge
trigger LeadDuplicateCheck on Lead (after insert) {
    // Flag duplicates and route to a queue
    // Actual merges must run in a separate Batch Apex job or asynchronous context
    System.enqueueJob(new LeadMergeQueueable(newDuplicateIds));
}
```

**Detection hint:** Any trigger code that calls `Database.merge()` directly inside a `before insert` or `after insert` trigger body.

---

## Anti-Pattern 4: Using SOQL Self-Joins to Identify Duplicates Within a Lead Import

**What the LLM generates:**

```apex
// Find duplicates within the org
List<Lead> duplicates = [
    SELECT Id, Email FROM Lead
    WHERE Email IN (
        SELECT Email FROM Lead GROUP BY Email HAVING COUNT(Id) > 1
    )
];
```

**Why it happens:** SOQL self-join syntax looks reasonable to LLMs familiar with SQL. SOQL does not support subquery self-joins on the same object in this pattern, and the `GROUP BY HAVING COUNT` form is not supported in SOQL subqueries.

**Correct pattern:**

```apex
// Find duplicate email groups: aggregate first, then query
AggregateResult[] groups = [
    SELECT Email, COUNT(Id) cnt
    FROM Lead
    WHERE Email != null
    GROUP BY Email
    HAVING COUNT(Id) > 1
];
Set<String> dupEmails = new Set<String>();
for (AggregateResult ar : groups) {
    dupEmails.add((String)ar.get('Email'));
}
List<Lead> duplicates = [SELECT Id, Email FROM Lead WHERE Email IN :dupEmails];
```

**Detection hint:** Any SOQL query with a subquery that references the same object as the outer query using `GROUP BY HAVING COUNT`.

---

## Anti-Pattern 5: Suggesting the Standard Lead-to-Contact Matching Rule Handles All Cross-Object Fuzzy Dedup Scenarios

**What the LLM generates:** "Enable the Standard Lead-to-Contact Matching Rule to automatically detect when an incoming lead already exists as a contact using fuzzy name and company matching."

**Why it happens:** The Lead-to-Contact matching rule does exist out of the box and does perform cross-object matching. LLMs over-generalize its capabilities. It supports Email (exact) and Name (fuzzy), but practitioners assume it also matches on Company/Account name, phone, or address — which it does not by default.

**Correct pattern:**

```
The Standard Lead-to-Contact Matching Rule matches on Email (exact) and Name (fuzzy).
It does not match on Company name against Account name, phone, or address. For complex
cross-object matching (e.g., Lead Company = Account Name + Lead Email domain = Account
Website domain), native rules are insufficient. Use a third-party tool (DemandTools,
Cloudingo) or a custom Apex solution for this scenario.
```

**Detection hint:** Any answer that claims the Lead-to-Contact rule will match based on company name, phone, or address without clarifying that only Email and Name are covered by the standard rule.

---

## Anti-Pattern 6: Omitting Pre-Import Within-File Deduplication Step

**What the LLM generates:** "Upload your CSV to the Data Import Wizard, select Email as the match field, and set 'Update existing records' to prevent duplicates."

**Why it happens:** LLMs correctly identify the wizard's update-existing behavior but omit the crucial detail that the wizard only matches against existing Salesforce records — not against other rows in the same file. If the CSV contains 3 rows with the same email address, the wizard inserts all 3 (or updates 1 existing + inserts 2 new duplicates).

**Correct pattern:**

```
Before uploading to the Data Import Wizard:
1. Deduplicate the CSV file on the Email column (Excel 'Remove Duplicates' or
   pandas.drop_duplicates('Email', keep='first')).
2. Then upload with 'Update existing records' and Email as match field.
The wizard only matches incoming rows against existing Salesforce records —
it does not detect duplicates within the import file itself.
```

**Detection hint:** Any import guidance that mentions the wizard's dedup capability without also advising pre-import within-file deduplication.
