# Examples — NPSP Household Accounts

## Example 1: Household Naming Customization for a Married Couple with Different Last Names

**Context:** A nonprofit org has donors Jane Smith and John Jones who are married but kept separate last names. They share a Household Account. The default NPSP naming produces "Jones Household" (alphabetical last Contact added), which does not reflect both donors.

**Problem:** Without custom naming configuration, only one last name appears in the household name and greeting fields, which affects mail merge accuracy and donor acknowledgment letters.

**Solution:**

Step 1 — Navigate to NPSP Settings > Households > Household Naming.

Step 2 — Set the following format strings:

```
Household Name Format:   {!LastName}
Name Connector:          " and "
Name Append Text:        " Household"

→ Result: "Smith and Jones Household"

Formal Greeting Format:  {!{!Salutation}} {!FirstName}} {!LastName}
Formal Greeting Connector: " and "

→ Result: "Ms. Jane Smith and Mr. John Jones"

Informal Greeting Format: {!FirstName}
Informal Greeting Connector: " and "

→ Result: "Jane and John"
```

Step 3 — Click "Refresh Household Names" in NPSP Settings to batch-regenerate all existing household names.

Step 4 — Verify the Household Account record for Jane Smith and John Jones now shows:
- Name: "Smith and Jones Household"
- Formal Greeting: "Ms. Jane Smith and Mr. John Jones"
- Informal Greeting: "Jane and John"

**Why it works:** NPSP evaluates the Name Format token across all Contacts in the household, concatenating with the configured connector. The `{!LastName}` token produces one value per household Contact, then joins them. The append text is added once at the end.

---

## Example 2: Merging Duplicate Household Accounts Using NPSP Flow

**Context:** A data import created duplicate Contact records for the same donor — "Robert Williams" appears twice, each on a separate Household Account. The original household has $5,000 in rollup giving; the duplicate has $0. A deduplication effort is underway.

**Problem:** Using the native Salesforce Account merge UI merges the Account records but bypasses NPSP Apex triggers. The surviving Account retains only the giving data from whichever master record was chosen — the $5,000 rollup may be lost or duplicated, Relationship records pointing at the deleted Contact become orphaned, and the household name may not regenerate correctly.

**Solution:**

Step 1 — Navigate to the duplicate **Contact** record (not the Account record).

Step 2 — Click "Find Duplicates" in the Contacts related list or use the NPSP Merge Duplicate Contacts quick action.

Step 3 — In the NPSP Merge Duplicate Contacts flow:
- Select the record to retain as the master Contact.
- Confirm which Household Account should be the surviving account.
- Review the field value selections for the merged Contact record.

Step 4 — Complete the flow. NPSP will:
- Merge the two Contact records
- Re-associate all Opportunity records with the surviving Contact and Household Account
- Re-fire household naming triggers to regenerate Account Name, Formal Greeting, and Informal Greeting
- Delete orphaned Relationship records pointing at the removed Contact

Step 5 — After the flow completes, verify on the surviving Household Account:

```
SELECT Id, Name, npo02__TotalOppAmount__c, npo02__NumberOfClosedOpps__c,
       npo02__Formal_Greeting__c, npo02__Informal_Greeting__c
FROM Account
WHERE Id = '<surviving_account_id>'
```

Confirm `npo02__TotalOppAmount__c` reflects the combined giving history.

**Why it works:** The NPSP Merge Duplicate Contacts flow uses NPSP's internal merge APIs which respect the trigger architecture. Rollup recalculation is triggered automatically on the surviving Account. Native merge does not invoke these APIs.

---

## Anti-Pattern: Using Native Account Merge for NPSP Households

**What practitioners do:** Navigate to the duplicate Account record in Salesforce, click the standard "Merge Accounts" button (or go to `/merge?mergeType=Account`), select a master record, and complete the native merge wizard.

**What goes wrong:** The native Salesforce Account merge bypasses all NPSP Apex triggers. The result is:
- Rollup fields (`npo02__TotalOppAmount__c`, `npo02__LastCloseDate__c`, etc.) reflect only the master Account's data — Opportunity history from the non-master is re-parented at the data layer but rollup totals are not recalculated
- `npe4__Relationship__c` records that referenced the deleted Contact ID become orphaned and cause errors in relationship views
- The household name may not regenerate because NPSP naming triggers were never fired during the merge
- The NPSP customization flag state from the non-master Account is silently discarded

**Correct approach:** Always merge duplicate NPSP Contacts (not Accounts directly) using the NPSP Merge Duplicate Contacts flow. If Account-only merges are needed for Organization Accounts (non-household), the standard merge UI is acceptable — but never for Household Account types.
