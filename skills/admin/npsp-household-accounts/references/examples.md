# Examples — NPSP Household Accounts

## Example 1: Household Naming for a Married Couple with Different Last Names

**Context:** A nonprofit org has donors Jane Smith and John Jones who are married but kept separate last names. They share a Household Account. Development staff expect the name to read "Smith and Jones Household" and the formal greeting to name both people.

**Problem:** Staff assume the default NPSP naming can only show one last name and start hand-editing household names. Each edit adds the field to `npo02__SYSTEM_CUSTOM_NAMING__c`, so those households stop updating forever.

**Solution:**

Step 1: Navigate to NPSP Settings > People > Households and read the current Household Naming settings before changing anything.

Step 2: Compare them with the NPSP defaults (set by `UTIL_CustomSettingsFacade.configHouseholdNamingSettings` in the NPSP source):

```text
Household Name Format:     {!LastName} Household
Formal Greeting Format:    {!{!Salutation} {!FirstName}} {!LastName}
Informal Greeting Format:  {!{!FirstName}}
Name Connector:            and          (one connector shared by all three strings;
                                         default comes from the npo02 HouseholdNameConnector label,
                                         UNVERIFIED (2026-10-03) that its value is "and")
Contact Overrun Count:     9
Implementing Class:        HH_NameSpec

Result for Jane Smith (Ms.) and John Jones (Mr.), Jane first in naming order:
  Name:               Smith and Jones Household
  Formal Greeting:    Ms. Jane Smith and Mr. John Jones
  Informal Greeting:  Jane and John
```

`HH_NameSpec` groups members by last name. Each distinct last name becomes one entry, entries are joined with the Name Connector, and the text after the last token (" Household") is appended once. The default format therefore already handles different last names. For Jane and John Smith it produces "Smith Household" and "Ms. Jane and Mr. John Smith".

Step 3: Set `npo02__Household_Naming_Order__c` to 0 on Jane and 1 on John if Jane must come first. Without it, NPSP puts the primary contact first, then the oldest record.

Step 4: If any household was hand-edited earlier, blank the overridden field on the Account and save, so NPSP takes it back. Then click "Refresh Household Names" in NPSP Settings to apply format changes to every household. Refresh skips fields that are still user-controlled.

Step 5: Verify the Household Account record shows the expected name and greetings.

**Why it works:** The format strings, not manual edits, carry the rule. The naming order makes the sequence deliberate. Releasing overridden fields lets the refresh reach every household.

---

## Example 2: Merging Duplicate Contacts Across Two Households

**Context:** A data import created duplicate Contact records for the same donor. "Robert Williams" appears twice, each on a separate Household Account. The original household has $5,000 in rollup giving; the duplicate has $0.

**Problem:** A volunteer merges the two Household Accounts with the native Account merge from a batch dedupe tool. The household name and `npo02__TotalOppAmount__c` on the survivor stay wrong for days. NPSP's Account merge handler only queues its fix-up when the merge is not running in a future or batch context.

**Solution:**

Step 1: Merge the duplicate Contacts, not the Accounts, with the NPSP Contact Merge page (Visualforce page `CON_ContactMerge`). Select two or three Contacts per pass.

Step 2: Choose the winning Contact and the field values to keep, then merge.

Step 3: NPSP's `CON_ContactMerge_TDTM` queues a fix-up job that updates household names and member counts and moves Opportunities for individual-account Contacts. Wait for the queueable job in Setup > Apex Jobs.

Step 4: Verify on the surviving Household Account:

```sql
SELECT Id, Name, npo02__TotalOppAmount__c, npo02__NumberOfClosedOpps__c,
       npo02__Formal_Greeting__c, npo02__Informal_Greeting__c,
       npo02__SYSTEM_CUSTOM_NAMING__c
FROM Account
WHERE Id = '<surviving_account_id>'
```

Confirm `npo02__TotalOppAmount__c` reflects the combined giving history. If the merge ran from a batch tool, re-run NPSP rollups for the surviving Accounts before reporting on them.

**Why it works:** Apex triggers fire on merge (delete events on losers, an update on the winner), but triggers do not fire on reparented children such as Opportunities (Apex Developer Guide, Triggers and Merge Statements). NPSP's merge handlers exist to repair what the merge itself does not, and they run asynchronously. Waiting for them, or re-running rollups when they were skipped, is what makes the totals correct.

---

## Anti-Pattern: Treating Native Account Merge as Either Safe or Forbidden Without Checking Context

**What practitioners do:** Either they merge Household Accounts with the native merge or a batch tool and report on totals immediately, or they ban native merge outright because "it bypasses NPSP triggers".

**What goes wrong:** The first group reports stale rollups, and from batch tools never gets the Account fix-up at all (`ACCT_AccountMerge_TDTM` skips it in future and batch contexts). The second group rejects a supported path based on a false premise and builds manual workarounds.

**Correct approach:** Prefer the NPSP Contact Merge page for small sets. For bulk tools, find out whether they merge in batch Apex, and plan a rollup re-run for survivors if they do. Always verify totals after the asynchronous jobs complete.

---

## Example 3: Deployable Custom Naming Class

The complete Apex class, its test, the `package.xml` entry, and audit queries are in `references/metadata-examples.md`. Use it only when the token syntax cannot express the naming rule.
