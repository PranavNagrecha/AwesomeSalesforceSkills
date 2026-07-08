# Examples: Duplicate Management

---

## Example: Blocking Contact Duplicates by Email

**Scenario:** Internal users create Contacts manually, and duplicate Contacts with the same business email cause confusion for sales reps.

**Decision:** Use a blocking duplicate rule on Contact with strong email-based matching.

**Why:** The confidence level is high enough that allowing save would create avoidable cleanup work.

---

## Example: Alerting on Account Name + Domain Similarity

**Scenario:** Account names vary slightly (`Acme Inc.`, `Acme Incorporated`, `Acme, Inc.`) and users sometimes add the same company twice.

**Decision:** Use a fuzzy or composite matching approach with steward review rather than hard blocking all saves.

**Why:** Business-account matching often needs human judgment, especially when subsidiaries or regional entities exist.

---

## Example: Merge Governance for Historical Cleanup

**Scenario:** The org already has thousands of duplicate Contacts. The business wants cleanup without losing useful values.

**Approach:**
1. define survivorship rules per field
2. assign a steward queue
3. merge in controlled batches
4. track duplicates found versus duplicates resolved

**Why this works:** It treats merges as governed remediation, not as random record deletion.

---

## Reference: What the Standard Fuzzy Methods Actually Do

"Use fuzzy matching" is not a design decision until you know which algorithms run and where they stop. Each standard method is a fixed algorithm set with a maximum match threshold — you choose the method, not the internals.

| Matching method | Algorithms | Max threshold |
|---|---|---|
| Exact | Exact | n/a |
| Fuzzy: First Name | Exact, Initials, Jaro-Winkler, Name Variant | 85 |
| Fuzzy: Last Name | Exact, Keyboard Distance, Metaphone 3 | 90 |
| Fuzzy: Company Name | Acronym, Exact, Syllable Alignment | 70 |
| Fuzzy: City | Edit Distance, Exact | 85 |
| Fuzzy: Street | Exact, Weighted Average, Edit Distance | 80 |
| Fuzzy: Phone | Exact, Weighted Average | 80 |
| Fuzzy: ZIP | Exact, Weighted Average | 80 |
| Fuzzy: Title | Acronym, Exact, Kullback-Liebler Distance | 50 |

**How to read this:**
- Exact works on almost any field, including custom fields. Everything else is field-shaped.
- Fuzzy: First Name is the only method carrying Name Variant, which is what gives you "Bob" against "Robert". If a matching rule includes Middle Name, that field is compared with Fuzzy: First Name too.
- Fuzzy: Last Name's tighter 90 threshold reflects that surnames carry more identity than given names. Metaphone 3 is a phonetic algorithm — it is doing English pronunciation, not string distance.
- Fuzzy: Company Name is loose by design at 70 because it strips "Inc" and "Corp" first and then compares syllables. This is what catches `Acme Inc.` against `Acme Incorporated`. The same looseness is why sibling entities and similarly-named unrelated companies are the method's characteristic false positive — test it against your own account names before trusting it to block.
- Fuzzy: Title at 50 is the loosest standard method. Never use it as a sole or leading match criterion.
- Fuzzy: Phone and Fuzzy: Street work best with North American data. See `gotchas.md`.

---

## Example: Letting an Integration Save Through an Alert

**Scenario:** A duplicate rule on Account is set to Alert so reps get a warning banner. A nightly Apex sync from the ERP now fails to insert legitimate subsidiary records, because Apex DML has no user sitting in front of it to acknowledge the alert.

**Decision:** Keep the rule. Set `allowSave` on the inserting transaction.

```apex
Database.DMLOptions dml = new Database.DMLOptions();
dml.DuplicateRuleHeader.allowSave = true;          // bypass the Alert, save anyway
dml.DuplicateRuleHeader.runAsCurrentUser = true;   // enforce the running user's sharing during matching

Account duplicateAccount = new Account(Name = 'dupe');
Database.SaveResult sr = Database.insert(duplicateAccount, dml);
if (sr.isSuccess()) {
    System.debug('Duplicate account has been inserted in Salesforce!');
}
```

**Why:** `allowSave` is the per-transaction answer to a rule that a human would have clicked through. It bypasses an Alert; it does not override a rule configured to Block — that behavior is set on the rule, not in Apex.

**What `runAsCurrentUser` decides:** whether sharing rules for the current user are enforced while duplicate rules run. Set it to `true` and matching respects what the running user can see, so users cannot be shown duplicate records that aren't available to them. Set it to `false` and matching evaluates without that constraint. This is the Apex-side counterpart of the rule's own bypass-sharing setting.

**The trap this closes:** setting the rule itself to Block "so nothing gets through" breaks every API and Apex insert path in the org, and `allowSave` cannot rescue them. Configure the rule for the strictest channel you can actually support, then relax per-transaction in Apex where a save is legitimate. Log every `allowSave` insert so the steward queue still learns about it.

---

## Example: Building a Steward Queue on DuplicateRecordSet

**Scenario:** Mode 2 review found the steward queue is a shared spreadsheet an analyst updates by hand from duplicate alert screenshots.

**Decision:** Read the queue from the objects Salesforce already populates.

**How it works:** A duplicate record set is a list of items identified as duplicates, created when a duplicate rule or a duplicate job runs. Each `DuplicateRecordSet` groups one or more `DuplicateRecordItem` records, one per record flagged as a duplicate. Both are standard objects, so the queue is a report, a list view, or a query — not a manual artifact.

```apex
// Records currently sitting in a given duplicate set, for a steward's merge screen.
List<DuplicateRecordItem> flagged = [
    SELECT Id, RecordId, DuplicateRecordSetId
    FROM DuplicateRecordItem
    WHERE DuplicateRecordSetId = :setId
];
```

**Why this works:**
1. Duplicate record sets that a rule never surfaced can still be created manually, so the queue covers the skip-list create paths too.
2. A custom report type over duplicate record sets and their items turns "how much duplicate debt do we have" into a dashboard instead of an argument.
3. Reporting on the sets is how you tune the rules. Volume by rule tells you which matching logic is too loose; sets that stewards consistently dismiss are your false-positive rate, measured rather than anecdotal.

Confirm field API names against the Object Reference before building the report type — the field set differs from the columns the Setup UI displays.
