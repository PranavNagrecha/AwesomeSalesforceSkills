# LLM Anti-Patterns — Record Type Strategy At Scale

Common mistakes AI coding assistants make when generating or advising on Record Type Strategy At Scale.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Hardcoding Record Type IDs

**What the LLM generates:**

```apex
Id rtId = '0124x000000AAAAMAA';
Case c = new Case(RecordTypeId = rtId, Subject = 'Test');
```

**Why it happens:** Training data contains code snippets copied from specific orgs. The LLM treats the ID as a stable constant because it appears as a string literal in many examples.

**Correct pattern:**

```apex
Id rtId = Schema.SObjectType.Case
    .getRecordTypeInfosByDeveloperName()
    .get('Support_Request')
    .getRecordTypeId();
Case c = new Case(RecordTypeId = rtId, Subject = 'Test');
```

**Detection hint:** Regex `['"][0-9a-zA-Z]{15,18}['"]` appearing as a RecordTypeId assignment. Any 15- or 18-character Salesforce ID literal assigned to a RecordTypeId field is suspect.

---

## Anti-Pattern 2: Using getRecordTypeInfosByName() Instead of getRecordTypeInfosByDeveloperName()

**What the LLM generates:**

```apex
Id rtId = Schema.SObjectType.Account
    .getRecordTypeInfosByName()
    .get('Enterprise Account')
    .getRecordTypeId();
```

**Why it happens:** `getRecordTypeInfosByName()` uses the Label (user-facing name), which can change with translations or admin edits. Many older training examples use this method because it predates widespread DeveloperName awareness.

**Correct pattern:**

```apex
Id rtId = Schema.SObjectType.Account
    .getRecordTypeInfosByDeveloperName()
    .get('Enterprise_Account')
    .getRecordTypeId();
```

**Detection hint:** Look for `getRecordTypeInfosByName()` calls. In almost all production code, `getRecordTypeInfosByDeveloperName()` is the correct choice because DeveloperName is locale-independent and stable.

---

## Anti-Pattern 3: Recommending a New Record Type When Dynamic Forms Suffices

**What the LLM generates:**

```text
"Create a new record type called 'VIP_Account' so that VIP accounts
show additional fields like VIP_Tier__c and Dedicated_Rep__c on the
page layout."
```

**Why it happens:** LLMs default to the most common documented solution (record types) without evaluating whether the use case requires picklist filtering or business process separation. Field visibility alone does not justify a new record type.

**Correct pattern:**

```text
"Add VIP_Tier__c and Dedicated_Rep__c to the existing page layout.
Use Dynamic Forms with a visibility rule: show these fields when
Customer_Segment__c = 'VIP'. No new record type is needed because
picklist values and business process are identical."
```

**Detection hint:** When the LLM recommends creating a record type, check if the stated reason is solely about showing or hiding fields. If no picklist filtering or business process difference is mentioned, Dynamic Forms is likely the better answer.

---

## Anti-Pattern 4: Ignoring the N x M Layout Assignment Impact

**What the LLM generates:**

```text
"Add a record type for each region: EMEA, APAC, Americas, ANZ.
This gives each region its own page layout."
```

**Why it happens:** The LLM does not model the multiplicative cost of layout assignments. Adding 4 record types to an org with 60 profiles creates 240 new layout assignment cells, but the LLM only considers the record type count in isolation.

**Correct pattern:**

```text
"Before adding record types, calculate the layout assignment impact:
4 new record types x 60 profiles = 240 new assignments. Evaluate
whether regional differences require distinct picklist values. If
the difference is only field visibility, use Dynamic Forms with a
Region__c-based visibility rule instead."
```

**Detection hint:** When the LLM suggests creating multiple record types, check if it also calculates or mentions the profile-multiplied layout assignment count. Absence of this analysis indicates the recommendation is incomplete.

---

## Anti-Pattern 5: Treating Dynamic Forms as a Security Control

**What the LLM generates:**

```text
"Use Dynamic Forms to hide the SSN__c field from standard users.
Set a visibility rule so only users with the 'View_Sensitive_Data'
permission see it."
```

**Why it happens:** Dynamic Forms visibility rules look like access controls in the UI, and LLMs conflate UI visibility with data security. Training data often describes Dynamic Forms alongside field-level security without clearly separating their enforcement layers.

**Correct pattern:**

```text
"Remove read access to SSN__c via field-level security (FLS) on
profiles or permission sets for users who should not see it.
Optionally, also use Dynamic Forms to improve UX by hiding the
(already FLS-protected) field from the page layout for users
who lack access."
```

**Detection hint:** If the LLM recommends Dynamic Forms for a field containing PII, financial data, or any sensitive information without also specifying FLS configuration, the recommendation has a security gap.

---

## Anti-Pattern 6: Forgetting to Update Record Type Picklist Overrides After Adding Global Values

**What the LLM generates:**

```text
"Add 'Platinum' to the Industry global value set. It will
automatically be available on all record types."
```

**Why it happens:** The LLM generalizes from field-level picklist behavior (where values are available everywhere by default) to record-type-filtered picklists (where values must be explicitly included in each record type's override). This distinction is subtle and underrepresented in training data.

**Correct pattern:**

```text
"Add 'Platinum' to the Industry global value set. Then update
each record type's picklist value override to include 'Platinum'
where appropriate. New global values are NOT automatically added
to record type picklist filters — they must be explicitly enabled
per record type."
```

**Detection hint:** Look for instructions to add picklist values to a global value set without a follow-up step to update record type picklist overrides. The phrase "automatically available" following a global value set change is a red flag.
