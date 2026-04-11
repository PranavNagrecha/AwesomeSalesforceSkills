# LLM Anti-Patterns — FSC Compliant Data Sharing API

Common mistakes AI coding assistants make when generating or advising on FSC Compliant Data Sharing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inserting AccountShare Directly with RowCause = 'CompliantDataSharing'

**What the LLM generates:**

```apex
AccountShare share = new AccountShare(
    AccountId     = accountId,
    UserOrGroupId = userId,
    AccessLevel   = 'Edit',
    RowCause      = 'CompliantDataSharing'
);
insert share;
```

**Why it happens:** LLMs trained on general Apex sharing patterns know that `AccountShare` is the share object for Account and that `RowCause` is a valid field. They infer that using the correct `RowCause` value mimics what CDS does, missing that the value is a restricted picklist reserved for platform-internal use.

**Correct pattern:**

```apex
AccountParticipant participant = new AccountParticipant(
    AccountId         = accountId,
    UserId            = userId,
    ParticipantRoleId = roleId
);
insert participant;
// The CDS engine writes AccountShare with RowCause = 'CompliantDataSharing' automatically
```

**Detection hint:** Search for `RowCause.*CompliantDataSharing` or `RowCause = 'CompliantDataSharing'` combined with `AccountShare` or `OpportunityShare` DML. Any such combination is the anti-pattern.

---

## Anti-Pattern 2: Treating Share Row Deletion as the Access Revocation Mechanism

**What the LLM generates:**

```apex
List<AccountShare> sharesToDelete = [
    SELECT Id FROM AccountShare
    WHERE AccountId = :accountId
    AND UserOrGroupId = :userId
    AND RowCause = 'CompliantDataSharing'
];
delete sharesToDelete;
```

**Why it happens:** Standard Apex managed sharing uses share row deletion to revoke access. LLMs apply the same pattern to CDS without knowing that CDS regenerates share rows from participant records on every recalculation.

**Correct pattern:**

```apex
List<AccountParticipant> participants = [
    SELECT Id FROM AccountParticipant
    WHERE AccountId = :accountId
    AND UserId = :userId
];
delete participants;
// CDS removes the AccountShare row on next recalculation pass
```

**Detection hint:** Look for `delete` DML targeting `AccountShare` or `OpportunityShare` with a `RowCause = 'CompliantDataSharing'` filter. This is revocation via the wrong control point.

---

## Anti-Pattern 3: Inserting AccountParticipant Without a ParticipantRoleId

**What the LLM generates:**

```apex
AccountParticipant participant = new AccountParticipant(
    AccountId = accountId,
    UserId    = userId
    // ParticipantRoleId omitted
);
insert participant;
```

**Why it happens:** LLMs familiar with junction objects assume that linking two IDs is sufficient. They miss that `ParticipantRoleId` is a required field that determines the `AccessLevel` written by the CDS engine to the share row. Omitting it causes a `REQUIRED_FIELD_MISSING` DML exception.

**Correct pattern:**

```apex
Id rmRoleId = [
    SELECT Id FROM ParticipantRole WHERE Name = 'Relationship Manager' LIMIT 1
].Id;
AccountParticipant participant = new AccountParticipant(
    AccountId         = accountId,
    UserId            = userId,
    ParticipantRoleId = rmRoleId
);
insert participant;
```

**Detection hint:** Search for `new AccountParticipant(` or `new OpportunityParticipant(` blocks that do not include `ParticipantRoleId =`. Any such block is missing the required field.

---

## Anti-Pattern 4: Asserting on AccountShare Rows Immediately After AccountParticipant Insert in Apex Tests

**What the LLM generates:**

```apex
@IsTest
static void testGrantAccess() {
    insert new AccountParticipant(
        AccountId = acct.Id, UserId = user.Id, ParticipantRoleId = roleId
    );
    List<AccountShare> shares = [
        SELECT Id FROM AccountShare
        WHERE AccountId = :acct.Id AND RowCause = 'CompliantDataSharing'
    ];
    System.assertEquals(1, shares.size(), 'Expected 1 CDS share row');
}
```

**Why it happens:** LLMs model CDS as synchronous, identical to standard Apex managed sharing where a share row is available immediately after insert. CDS processing is asynchronous; the assertion runs in the same transaction as the insert and returns zero rows.

**Correct pattern:**

```apex
@IsTest
static void testGrantAccess() {
    Test.startTest();
    insert new AccountParticipant(
        AccountId = acct.Id, UserId = user.Id, ParticipantRoleId = roleId
    );
    Test.stopTest(); // flushes async CDS processing
    List<AccountShare> shares = [
        SELECT Id FROM AccountShare
        WHERE AccountId = :acct.Id AND RowCause = 'CompliantDataSharing'
    ];
    System.assertEquals(1, shares.size(), 'Expected 1 CDS share row');
}
```

**Detection hint:** Search for `AccountShare` SOQL queries in `@IsTest` methods that appear after `AccountParticipant` or `OpportunityParticipant` inserts but outside of a `Test.stopTest()` boundary.

---

## Anti-Pattern 5: Using Standard RowCause = 'Apex' as a CDS Workaround in FSC Orgs

**What the LLM generates:**

```apex
// "Workaround for CDS — use Apex row cause instead"
AccountShare share = new AccountShare(
    AccountId     = accountId,
    UserOrGroupId = userId,
    AccessLevel   = 'Edit',
    RowCause      = Schema.AccountShare.rowCause.Apex
);
insert share;
```

**Why it happens:** An LLM aware that `RowCause = 'CompliantDataSharing'` is restricted may suggest `RowCause = 'Apex'` as the next best option. In a non-FSC org this would be a valid Apex managed sharing pattern. In a CDS-enabled FSC org it creates share rows outside the CDS system, which are invisible to FSC compliance audit queries, survive recalculation independently, and may produce confusing double-share entries if CDS also grants access for the same user.

**Correct pattern:**

```apex
// In a CDS-enabled FSC org, all Account sharing must flow through participant records
AccountParticipant participant = new AccountParticipant(
    AccountId         = accountId,
    UserId            = userId,
    ParticipantRoleId = roleId
);
insert participant;
```

**Detection hint:** In a CDS-enabled FSC org, any `AccountShare` insert with `RowCause = Schema.AccountShare.rowCause.Apex` or `RowCause = 'Apex'` targeting objects that have CDS enabled is a CDS bypass. Flag these for review.

---

## Anti-Pattern 6: Assuming CDS Is Enabled Without Checking IndustriesSettings

**What the LLM generates:** Advice or code that inserts `AccountParticipant` records and asserts that CDS access will be granted, without mentioning or checking whether CDS is enabled in the org's IndustriesSettings metadata.

**Why it happens:** LLMs treat FSC and CDS as synonymous. In reality, CDS is an optional feature within FSC that requires explicit enablement via IndustriesSettings (`enableCompliantDataSharingForAccount`, etc.). An FSC org without CDS enabled will accept `AccountParticipant` inserts without error but will never write the corresponding share rows.

**Correct pattern:** Always include a prerequisite check or documentation step that verifies CDS is enabled before generating participant record DML. In org troubleshooting scenarios, query or advise the practitioner to verify `IndustriesSettings` in the org's deployed metadata:

```xml
<!-- In IndustriesSettings.settings-meta.xml -->
<enableCompliantDataSharingForAccount>true</enableCompliantDataSharingForAccount>
```

**Detection hint:** Any CDS-related code generation that does not reference IndustriesSettings verification, OWD requirements, or API version prerequisites is incomplete and may silently fail in orgs where CDS has not been activated.
