# FSC Compliant Data Sharing API — Work Template

Use this template when working on tasks that involve granting or revoking record-level access in a Financial Services Cloud org using Compliant Data Sharing (CDS).

---

## Scope

**Skill:** `fsc-compliant-sharing-api`

**Request summary:** (fill in what the user asked for)

---

## Prerequisites Verified

Before writing any code, confirm:

- [ ] CDS is enabled for the target object in IndustriesSettings:
  - Account: `enableCompliantDataSharingForAccount = true`
  - Opportunity: `enableCompliantDataSharingForOpportunity = true`
  - Custom objects: `enableCompliantDataSharingForCustomObjects = true` AND per-object flag
- [ ] OWD for the target object: ____________________  (must be Private or Public Read Only)
- [ ] API version in use: ____________________ (must be 50.0+)
- [ ] ParticipantRole IDs gathered (see query below)

**ParticipantRole lookup query:**

```soql
SELECT Id, Name FROM ParticipantRole ORDER BY Name
```

Role name needed: ____________________
Role ID: ____________________

---

## Access Grant Pattern

Select the applicable pattern:

- [ ] Single-user grant — insert `AccountParticipant` with `UserId`
- [ ] Group/team grant — insert `AccountParticipant` with `ParticipantGroup.Id` in `UserId` field
- [ ] Opportunity access — insert `OpportunityParticipant`

**Participant record template:**

```apex
// Replace placeholders with actual values
AccountParticipant participant = new AccountParticipant(
    AccountId         = /* Account ID */,
    UserId            = /* User ID or ParticipantGroup ID */,
    ParticipantRoleId = /* ParticipantRole ID from lookup above */
);
Database.insert(new List<AccountParticipant>{ participant }, false);
```

---

## Access Revocation Pattern

```apex
// Revoke by deleting the AccountParticipant record — NOT by deleting AccountShare
List<AccountParticipant> toRevoke = [
    SELECT Id FROM AccountParticipant
    WHERE AccountId = :targetAccountId
    AND UserId = :targetUserId
];
delete toRevoke;
```

---

## Verification Query

After participant insert (allow async delay; in tests use Test.stopTest() first):

```soql
SELECT Id, UserOrGroupId, AccessLevel, RowCause
FROM AccountShare
WHERE AccountId = '<account-id>'
  AND RowCause = 'CompliantDataSharing'
```

Expected result: one row per participant with `RowCause = 'CompliantDataSharing'`.

---

## ParticipantGroup Bulk Pattern (Teams/Branches)

```apex
// 1. Lookup or create the group
ParticipantGroup group = new ParticipantGroup(Name = '/* Group Name */');
insert group;

// 2. Add members
List<ParticipantGroupMember> members = new List<ParticipantGroupMember>();
for (Id userId : teamMemberIds) {
    members.add(new ParticipantGroupMember(
        ParticipantGroupId = group.Id,
        UserId             = userId
    ));
}
insert members;

// 3. One AccountParticipant per account referencing the group
List<AccountParticipant> participants = new List<AccountParticipant>();
for (Id accountId : accountIds) {
    participants.add(new AccountParticipant(
        AccountId         = accountId,
        UserId            = group.Id,  // group ID, not a user ID
        ParticipantRoleId = /* role ID */
    ));
}
Database.insert(participants, false);
```

---

## Checklist

- [ ] CDS enabled in IndustriesSettings for all targeted objects
- [ ] OWD is Private or Public Read Only
- [ ] All participant inserts include `ParticipantRoleId`
- [ ] Access revocation uses participant record deletion, not share row deletion
- [ ] Apex tests wrap participant DML in `Test.startTest()` / `Test.stopTest()`
- [ ] No direct `AccountShare` / `OpportunityShare` insert or delete DML in scope
- [ ] Bulk patterns use `ParticipantGroup` when team membership is dynamic
- [ ] Checker script run: `python3 scripts/check_fsc_compliant_sharing_api.py --manifest-dir <path>`

---

## Notes

Record any deviations from the standard CDS pattern and why:

(fill in)
