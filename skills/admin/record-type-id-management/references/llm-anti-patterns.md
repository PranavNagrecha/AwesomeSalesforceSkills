# LLM Anti-Patterns — Record Type ID Management

Common mistakes AI coding assistants make when handling record-type references.

## Anti-Pattern 1: Hard-coding an 18-char record-type ID in Apex

**What the LLM generates:** `if (acc.RecordTypeId == '012Hs000000ABcDEFG') { ... }`

**Why it happens:** The model copies an ID seen in a specific org; not aware IDs are org-specific.

**Correct pattern:**

```
Id businessId = Schema.SObjectType.Account
    .getRecordTypeInfosByDeveloperName()
    .get('Business_Account').getRecordTypeId();
if (acc.RecordTypeId == businessId) { ... }
```

**Detection hint:** Apex source with `012[A-Za-z0-9]{12,15}` literals, especially in comparisons.

---

## Anti-Pattern 2: Referencing RecordType.Name instead of DeveloperName

**What the LLM generates:** `WHERE RecordType.Name = 'Business Account'` in SOQL or `$RecordType.Name = 'Business Account'` in a formula.

**Why it happens:** Name is user-visible and feels natural.

**Correct pattern:**

```
Admins rename labels. DeveloperName is the API handle. Use
RecordType.DeveloperName or $RecordType.DeveloperName; comparisons
survive label changes and translation.
```

**Detection hint:** SOQL `WHERE RecordType.Name = ...` or formulas referencing `$RecordType.Name`.

---

## Anti-Pattern 3: Passing record-type ID from Apex to LWC as a literal

**What the LLM generates:** An `@AuraEnabled` method returns a hard-coded Id string for the LWC to use.

**Why it happens:** The model pushes the hard-coded value behind a method without changing its shape.

**Correct pattern:**

```
Resolve on the client with getObjectInfo wire, or return DeveloperName
from Apex and look up on the client. Never ship an ID string from
Apex unless it was resolved by Schema.describe in the same transaction.
```

**Detection hint:** `@AuraEnabled` method returning a string literal that looks like a record-type ID.

---

## Anti-Pattern 4: Caching record-type ID in a static variable that survives across orgs

**What the LLM generates:** Managed package code with `static final Id RT = '012...';` at class load.

**Why it happens:** The model applies static-field caching without realizing package installs into many orgs.

**Correct pattern:**

```
Static initializers run per transaction, but the hard-coded value
baked into the class is the same everywhere. Resolve via describe in
a static initializer or lazy-init method:

private static Id RT { get { if (RT == null) RT = Schema...; return RT; } }
```

**Detection hint:** Any `static final Id` field in Apex initialized to an 18-char literal.

---

## Anti-Pattern 5: Filtering by record-type ID in a reports/list view formula

**What the LLM generates:** List view criteria with `RecordTypeId equals 012Hs0000001abc`.

**Why it happens:** The admin-facing UI suggests ID filters; model copies the pattern.

**Correct pattern:**

```
Filter list views, reports, and dashboards by Record Type (the
picklist UI gives name). In formulas, use DeveloperName. List views
persist the internal Id but show the name — still okay for list
views; but formulas and validation rules must use DeveloperName.
```

**Detection hint:** Formula metadata with `RecordTypeId = "012..."`.
