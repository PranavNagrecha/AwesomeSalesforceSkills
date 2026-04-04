# Gotchas — Person Accounts

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Enablement Is Permanent — There Is No Off Switch

**What happens:** Once Person Accounts is enabled in a Salesforce org, it cannot be disabled. The `IsPersonAccount` field becomes permanently available on Account, the Person Account record type designation persists, and any Person Account records in the org remain as-is. Salesforce Support will not reverse Person Account enablement.

**When it occurs:** Organizations sometimes enable Person Accounts in a sandbox to evaluate the feature, then inadvertently enable it in production without full impact analysis — or enable it under time pressure without properly assessing AppExchange package compatibility or existing code.

**How to avoid:** Treat Person Account enablement as a one-way architectural decision. Before requesting enablement in any production or persistent sandbox:
1. Run full impact analysis on all Apex, Flows, and installed packages.
2. Get explicit sign-off from technical architect and product owner.
3. Enable in a developer sandbox first, run all test suites, and test all integrations.
4. Document the decision and the date — future team members need to understand why the org is configured this way.

---

## Gotcha 2: Apex `IsPersonAccount` Is Null in `before insert` Context

**What happens:** In a `before insert` trigger on the Account object, the `IsPersonAccount` field is not yet populated by the platform. It evaluates to `null`, not `false`. Any logic that checks `if (acc.IsPersonAccount)` in a `before insert` trigger silently does nothing for newly inserted Person Accounts.

**When it occurs:** Trigger code that needs to initialize or validate Person Account-specific fields (PersonEmail format, PersonBirthdate ranges, etc.) during insert. The developer tests in `before update` where `IsPersonAccount` is already set, but the `before insert` path is never triggered correctly.

**How to avoid:** In `before insert` context, check the `RecordTypeId` field instead of `IsPersonAccount`:
```apex
Set<Id> personAccountRtIds = getPersonAccountRecordTypeIds(); // load once
for (Account acc : Trigger.new) {
    Boolean isPersonAccount = personAccountRtIds.contains(acc.RecordTypeId);
    if (isPersonAccount) {
        // safe to use PersonEmail, PersonPhone, etc.
    }
}
```
Reserve `IsPersonAccount` checks for `before update`, `after insert`, and `after update` contexts where the platform has already committed the value.

---

## Gotcha 3: SOQL on Contact Returns PersonContact Records Silently

**What happens:** When Person Accounts is enabled, every Person Account has a system-managed PersonContact record linked via `PersonContactId`. These PersonContact records appear in all `SELECT ... FROM Contact` queries without any indication they are system-managed records. Code that processes Contact query results will encounter PersonContact records and may update, delete, or sync them as if they were regular Contacts.

**When it occurs:** Existing Contact-based Apex, batch jobs, reports, and integrations that predate Person Account enablement. Also affects any newly written code that is not Person Account-aware.

**How to avoid:** Add an explicit filter to any Contact query that should not return PersonContact records:
```soql
SELECT Id, FirstName, LastName, Email, AccountId
FROM Contact
WHERE Account.IsPersonAccount = false
```
In Apex triggers on Contact, add a guard at the start of the trigger:
```apex
List<Contact> regularContacts = new List<Contact>();
for (Contact c : Trigger.new) {
    if (!c.Account.IsPersonAccount) {
        regularContacts.add(c);
    }
}
if (regularContacts.isEmpty()) return;
```
Note: accessing `Account.IsPersonAccount` in a trigger requires the Account to be in the trigger query context (not always available in `before insert`).

---

## Gotcha 4: AppExchange Packages That Assume All Accounts Have Child Contacts

**What happens:** Many AppExchange packages were built before Person Accounts were widely adopted. These packages often iterate over Contacts by querying with `AccountId` filters, assume that Account records always have at least one child Contact, or attempt to insert Contact records linked to Account records. When these packages encounter Person Account records, they either throw exceptions (attempting to insert a Contact with a Person Account's AccountId) or silently skip records, producing incomplete data.

**When it occurs:** Any time an installed package executes its logic against Account or Contact records in an org that has Person Accounts enabled. Common culprits: CPQ packages, marketing automation integrations, data quality tools, and field service add-ons.

**How to avoid:** Before enabling Person Accounts, inventory all installed AppExchange packages and verify each vendor's documented Person Account support status. Contact the ISV if support status is unclear. For packages that do not support Person Accounts, evaluate whether they can be scoped to Business Accounts only via record type filters, or whether the package must be replaced.

---

## Gotcha 5: Duplicate Management Needs Separate Rules for Person Accounts and Business Accounts

**What happens:** Salesforce Duplicate Management (Duplicate Rules + Matching Rules) treats Person Accounts and Business Accounts as the same sObject type (Account). A duplicate rule that runs on Account records will fire for both types unless it is specifically filtered. A matching rule built on `Name` + `BillingCity` may incorrectly flag a Person Account named "Acme LLC" (used for a person, not a business) as a duplicate of a Business Account named "Acme LLC."

**When it occurs:** Orgs that enable Person Accounts without updating their existing Duplicate Rules. Also occurs when Duplicate Rules are built without an `Is Person Account` condition, causing cross-type false positives.

**How to avoid:** Create separate Duplicate Rules for Person Accounts and Business Accounts:
- For Person Accounts: match on `PersonEmail`, `PersonPhone`, `FirstName + LastName + PersonBirthdate`.
- For Business Accounts: match on `Name`, `BillingCity`, `Phone`, `Website`.
- Add a `Record Type` or `Is Person Account` filter condition to each rule so that Business Account rules do not fire on Person Account records and vice versa.

---

## Gotcha 6: Merging Person Accounts with Business Accounts Is Blocked

**What happens:** Salesforce prevents merging a Person Account with a Business Account. The merge UI and the `merge` DML statement in Apex both enforce this constraint. If a data quality process identifies duplicates across account types (one Person Account and one Business Account representing the same person), the merge tool cannot resolve the duplication automatically.

**When it occurs:** In mixed B2B+B2C orgs where an individual exists both as a Person Account (created correctly) and as a Business Account (created incorrectly, perhaps before a Person Account was set up). Automated deduplication tools may flag these as duplicates but be unable to merge them.

**How to avoid:** Ensure data entry and integration processes always create individuals as Person Accounts (not Business Accounts). Use Duplicate Rules to prevent creation of Business Accounts with the same name/email as existing Person Accounts. If cross-type duplicates already exist, resolve them manually: copy data from the incorrect record to the correct one, then delete the incorrect record — there is no merge shortcut.
