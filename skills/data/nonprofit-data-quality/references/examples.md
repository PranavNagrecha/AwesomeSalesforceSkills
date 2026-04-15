# Examples — Nonprofit Data Quality

## Example 1: Retroactive Address Verification After Enabling SmartyStreets Integration

**Context:** A 40,000-constituent NPSP org enabled SmartyStreets address verification six months after initial data load. The integration is correctly configured under NPSP Settings > Address Settings, and new records are being verified automatically. However, 38,000 existing `npsp__Address__c` records still show `npsp__Verified__c = false` because they predate the integration setup.

**Problem:** The fundraising team is preparing a direct mail campaign and needs postal-quality addresses. Running a SOQL query reveals almost no records are verified. A developer adds verification code to a Flow that updates Contact mailing fields — but NPSP overwrites those fields on the next synchronization cycle, and the actual `npsp__Address__c` records remain unverified.

**Solution:**

The correct fix is to execute the NPSP batch class that processes `npsp__Address__c` records through the configured verification service:

```apex
// Execute in Developer Console > Anonymous Apex
// This enqueues the NPSP address verification batch for all unverified records
ADDR_Addresses_TDTM batch = new ADDR_Addresses_TDTM();
// Run with a manageable batch size to stay within external callout limits
Database.executeBatch(batch, 25);
```

To monitor progress:
```apex
// Check batch status after submission
List<AsyncApexJob> jobs = [
    SELECT Id, Status, JobItemsProcessed, TotalJobItems, NumberOfErrors
    FROM AsyncApexJob
    WHERE ApexClass.Name = 'ADDR_Addresses_TDTM'
    ORDER BY CreatedDate DESC
    LIMIT 5
];
for (AsyncApexJob j : jobs) {
    System.debug(j.Status + ' — ' + j.JobItemsProcessed + '/' + j.TotalJobItems);
}
```

After the batch completes, verify coverage:
```soql
SELECT npsp__Verified__c, COUNT(Id)
FROM npsp__Address__c
GROUP BY npsp__Verified__c
```

**Why it works:** The `ADDR_Addresses_TDTM` trigger handler is the NPSP-native path for processing address verification through the configured integration. Running it as a batch ensures every existing `npsp__Address__c` record is sent through the verification service, populating `npsp__Verified__c`, `npsp__Verification_Status__c`, and geocoding fields. A batch size of 25 avoids hitting per-transaction callout limits imposed on external HTTP callouts.

---

## Example 2: Merging Duplicate Household Contacts After a Fundraising Event Import

**Context:** An annual gala import created 150 duplicate Contacts — existing donors who registered under slightly different names or email addresses. A data steward attempts to use the standard Salesforce Contacts list view "Merge Contacts" feature to clean up the duplicates. After merging 20 pairs, the fundraising manager notices that the Household Accounts for merged Contacts now show incorrect `npo02__TotalOppAmount__c` values — some show $0 when they should show thousands of dollars in donation history.

**Problem:** The native Salesforce Contact merge invoked `Database.merge()` under the hood, which does not fire NPSP's TDTM trigger framework. Rollup recalculation handlers were never invoked. The Household Account's rollup fields are now stale.

**Solution:**

For the remaining duplicate pairs, use the NPSP Contact Merge page instead:

1. Navigate to the winning Contact record.
2. In the page layout, click the **Merge Contacts** button (NPSP-installed action), which opens `/apex/NPSP__merge?id={ContactId}`.
3. Search for the duplicate record and select it as the losing Contact.
4. Review field-level selection (choose which values to retain) and click Merge.
5. Confirm that rollup fields recalculate on the Household Account.

For the 20 already-incorrectly-merged records, trigger a manual rollup recalculation:

```apex
// Recalculate rollups for affected Household Account IDs
// Run in Developer Console > Anonymous Apex
Set<Id> affectedAccountIds = new Set<Id>{
    '001xxxxxxxxxxxxxxx', // Replace with actual Account IDs
    '001yyyyyyyyyyyyyyy'
};
RLLP_OppRollup_UTIL rollupUtil = new RLLP_OppRollup_UTIL();
RLLP_OppRollup rollup = new RLLP_OppRollup(rollupUtil);
rollup.rollupAccounts(affectedAccountIds);
```

**Why it works:** NPSP Contact Merge fires the full TDTM handler chain, including `RLLP_OppRollup` for recalculating giving totals, `REL_Relationships_TDTM` for consolidating relationship records, and household address synchronization. The native Salesforce merge skips all of these, leaving the Household Account in an inconsistent state.

---

## Anti-Pattern: Using Standard Salesforce Duplicate Rules as the Primary NPSP Duplicate Gate

**What practitioners do:** Configure a standard Salesforce Duplicate Rule on the Contact object with matching criteria on First Name, Last Name, and Email. Expect it to catch all duplicate Contacts during NPSP Data Importer runs.

**What goes wrong:** Standard Salesforce Duplicate Rules fire on Contact insert/update via the standard platform duplicate detection framework. The NPSP Data Importer works through the `npsp__DataImport__c` staging object — records are written to that staging object first and then processed in batch. The Duplicate Rule fires when the Contact is eventually created from staging, but at that point the match is post-creation, not pre-creation. Additionally, standard Duplicate Rules do not apply the NPSP Contact Matching logic that groups Contacts by household, meaning a husband and wife with the same last name can be flagged as duplicates of each other incorrectly.

**Correct approach:** Configure **NPSP Contact Matching Rules** under NPSP Settings > Contacts as the primary prevention gate for imports via the NPSP Data Importer. For other insert paths (forms, APIs), implement duplicate checking at the integration layer before records reach Salesforce.
