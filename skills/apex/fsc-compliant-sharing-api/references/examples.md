# Examples — FSC Compliant Data Sharing API

## Example 1: Grant a Relationship Manager Access to an Account on Assignment

**Context:** A trigger fires on `AccountTeamMember__c` (a custom FSC junction object) when a banker is assigned to an account. The banker needs Read/Edit access to the Account record immediately. CDS is enabled for Account; OWD is Private.

**Problem:** A developer unfamiliar with FSC inserts an `AccountShare` row directly with `RowCause = 'Apex'`. The share works initially but is invisible to the CDS audit trail and will be orphaned from the CDS recalculation cycle. If OWD changes or an admin triggers recalculation, the manual share row may conflict with or be superseded by a CDS-managed share, resulting in confusing duplicate rows or access gaps.

**Solution:**

```apex
// Query the ParticipantRole for 'Relationship Manager'
List<ParticipantRole> roles = [
    SELECT Id FROM ParticipantRole
    WHERE Name = 'Relationship Manager'
    LIMIT 1
];
if (roles.isEmpty()) {
    throw new AuraHandledException('ParticipantRole "Relationship Manager" not found.');
}
Id rmRoleId = roles[0].Id;

// Build AccountParticipant records from the triggering junction records
List<AccountParticipant> participants = new List<AccountParticipant>();
for (AccountTeamMember__c assignment : Trigger.new) {
    participants.add(new AccountParticipant(
        AccountId         = assignment.Account__c,
        UserId            = assignment.Banker__c,
        ParticipantRoleId = rmRoleId
    ));
}

// Insert with partial-success to handle duplicates gracefully
Database.SaveResult[] results = Database.insert(participants, false);
for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) {
        Database.Error err = results[i].getErrors()[0];
        if (err.getStatusCode() != StatusCode.DUPLICATE_VALUE) {
            // Only log non-duplicate failures — duplicates are expected on re-assignment
            System.debug(LoggingLevel.ERROR,
                'CDS participant insert failed: ' + err.getMessage());
        }
    }
}
```

**Why it works:** Inserting `AccountParticipant` is the correct CDS API surface. The platform's CDS engine writes `AccountShare` with `RowCause = 'CompliantDataSharing'` automatically. The grant survives recalculation because the participant record is the source of truth, not the share row. Using `Database.insert(list, false)` allows the bulk trigger to continue if one participant already exists (e.g., reassignment to the same banker).

---

## Example 2: Bulk Team Access via ParticipantGroup During a Branch Reorganization

**Context:** A bank merges two branches. Branch A had 30 bankers, each with `AccountParticipant` records across 2,000 accounts — 60,000 participant records total. The merged Branch AB team now has 45 bankers and should have access to all 4,000 combined accounts. Managing per-user, per-account participant records at scale is untenable.

**Problem:** A developer writes a batch job that deletes 60,000 old `AccountParticipant` records and inserts 90,000 new ones (45 users × 2,000 accounts per branch). This is 150,000 DML rows across multiple batch executes and creates an enormous ongoing maintenance burden as team membership continues to change.

**Solution:**

```apex
// Step 1: Create a single ParticipantGroup for the merged branch
ParticipantGroup branchGroup = new ParticipantGroup(
    Name = 'Branch AB - Relationship Managers'
);
insert branchGroup;

// Step 2: Add all 45 bankers as ParticipantGroupMembers
List<ParticipantGroupMember> members = new List<ParticipantGroupMember>();
for (Id bankerId : branchABBankerIds) {
    members.add(new ParticipantGroupMember(
        ParticipantGroupId = branchGroup.Id,
        UserId             = bankerId
    ));
}
insert members;

// Step 3: Query the Participant Role for branch-level access
Id branchRoleId = [
    SELECT Id FROM ParticipantRole WHERE Name = 'Branch Member' LIMIT 1
].Id;

// Step 4: Insert ONE AccountParticipant per account referencing the group
//         (not one per banker — the group handles fan-out)
List<AccountParticipant> groupParticipants = new List<AccountParticipant>();
for (Id accountId : allBranchAccountIds) {
    groupParticipants.add(new AccountParticipant(
        AccountId         = accountId,
        UserId            = branchGroup.Id,  // polymorphic — accepts Group IDs
        ParticipantRoleId = branchRoleId
    ));
}
Database.insert(groupParticipants, false);

// Future membership change: just add/remove ParticipantGroupMember records
// No AccountParticipant changes needed — CDS updates share rows automatically
ParticipantGroupMember newMember = new ParticipantGroupMember(
    ParticipantGroupId = branchGroup.Id,
    UserId             = newBankerId
);
insert newMember;  // CDS grants access to all 4,000 accounts automatically
```

**Why it works:** Instead of 90,000 per-user participant records, the merged branch has 4,000 `AccountParticipant` records — one per account — referencing the group. CDS evaluates group membership at recalculation time and writes share rows for all current members. A future team change only requires a single `ParticipantGroupMember` insert or delete, not thousands of participant record updates.

---

## Anti-Pattern: Writing Directly to AccountShare with RowCause = 'CompliantDataSharing'

**What practitioners do:** A developer familiar with Apex managed sharing inserts `AccountShare` rows directly, using `RowCause = 'CompliantDataSharing'` to match what the CDS engine produces.

**What goes wrong:** The platform reserves `RowCause = 'CompliantDataSharing'` for internal use by the CDS engine. A direct `insert` of an `AccountShare` row with this row cause throws:

```
System.DmlException: Insert failed. First exception on row 0; 
first error: INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST, 
RowCause: bad value for restricted picklist field: CompliantDataSharing
```

Even if the DML somehow succeeded in a misconfigured org, the share row would be overwritten or deleted the next time the CDS recalculation engine runs, because the engine rebuilds shares exclusively from participant records — not from existing share rows.

**Correct approach:** Insert `AccountParticipant` or `OpportunityParticipant` records. The CDS engine writes and manages all `AccountShare` / `OpportunityShare` rows with `RowCause = 'CompliantDataSharing'` automatically.
