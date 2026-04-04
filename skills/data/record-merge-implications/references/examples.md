# Examples — Record Merge Implications

## Example 1: Account Merge Loses Custom Field Value from Losing Record

**Scenario:** A data team uses `Database.merge()` in Apex to merge duplicate Account records as part of a bulk deduplication job. One losing Account has a custom field `Annual_Revenue_Verified__c` set to `true`, while the master Account has it as `null`. After the merge, `Annual_Revenue_Verified__c` on the master is still `null` — the value from the losing record was not carried over.

**Root cause:** `Database.merge()` keeps the master record's existing field values. Fields that are null on the master and non-null on the losing record are not automatically populated — unlike the UI merge which allows field selection.

**Fix:**
```apex
// Before calling Database.merge(), copy needed fields from losing record
Account losingAccount = [SELECT Annual_Revenue_Verified__c FROM Account WHERE Id = :losingId LIMIT 1];
if (losingAccount.Annual_Revenue_Verified__c == true && masterAccount.Annual_Revenue_Verified__c != true) {
    masterAccount.Annual_Revenue_Verified__c = true;
    update masterAccount;
}
Database.merge(masterAccount, losingId);
```

**Result:** The master Account has the correct `Annual_Revenue_Verified__c` value after merge.

---

## Example 2: Merge Triggers Record-Triggered Flow Unexpectedly

**Scenario:** A Record-Triggered Flow on Contact fires "after update" to send a welcome email when a Contact's `Email` field is populated. After merging two Contact records where the losing Contact had an email but the master did not, the Flow fired and sent an unexpected welcome email to the merged Contact — even though this was a merge, not a new contact creation.

**Root cause:** The merge is processed as an update to the master Contact record. When the master Contact's `Email` field changes (from null to the value selected from the losing Contact), the Record-Triggered Flow's criteria are met and it fires.

**Fix:** Add an entry condition to the Flow: `ISCHANGED(Email) AND CreatedDate = TODAY` — or more robustly, check a custom field `Welcome_Email_Sent__c` as a guard to prevent duplicate sends. Alternatively, exclude merge contexts by checking if the record's `IsMerged__c` (if a tracking field exists) is true before proceeding.

**Note:** There is no native `$Record.IsMerge` variable in Flow — the merge is indistinguishable from a normal update at the Flow execution level. Defensive entry criteria are the correct mitigation.

---

## Example 3: OwnerId Reverts to Master Record's Owner Despite UI Selection

**Scenario:** A sales ops user merges two duplicate Leads. The losing Lead's owner is the correct sales rep for this prospect, but the master Lead belongs to a different rep. During the UI merge, the user assumes they can select the losing Lead's Owner from the field selection screen. After merge, the master Lead's original owner remains — the selection for Owner had no effect.

**Root cause:** `OwnerId` is a non-user-selectable field in the merge UI. Salesforce always retains the master record's `OwnerId` regardless of what appears on the merge screen. The Owner field may appear in the UI but its value cannot be overridden by selecting the losing record's value.

**Fix:** Before initiating the merge, update the master Lead's `OwnerId` to the desired owner:
```apex
masterLead.OwnerId = correctOwnerId;
update masterLead;
Database.merge(masterLead, losingLeadId);
```

Or in the UI: edit the master Lead's Owner field before proceeding to the merge screen.
