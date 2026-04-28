# LLM Anti-Patterns — Permission Set Group Composition

Common mistakes AI coding assistants make when generating, refactoring, or advising on Permission Set Group composition. These help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Cloning a PSG to make a small variant instead of using a Mute Permission Set

**What the LLM generates:**

```text
"I will create PSG_SalesManager_Prod by cloning PSG_SalesRep_Prod and removing
PS_OpportunityDelete from the included permission sets."
```

**Why it happens:** The LLM defaults to "make a copy and edit it" because that mental model is dominant in non-Salesforce training data (file copies, branches, configuration overrides). The mute primitive is Salesforce-specific and undertrained.

**Correct pattern:**

```xml
<!-- PSG_SalesRep_Prod.permissionsetgroup-meta.xml — unchanged -->
<PermissionSetGroup>
    <permissionSets>PS_OpportunityRead</permissionSets>
    <permissionSets>PS_OpportunityCreate</permissionSets>
    <permissionSets>PS_OpportunityEdit</permissionSets>
    <permissionSets>PS_OpportunityDelete</permissionSets>
</PermissionSetGroup>

<!-- PSG_SalesManager_Prod.permissionsetgroup-meta.xml — same PSes + mute -->
<PermissionSetGroup>
    <permissionSets>PS_OpportunityRead</permissionSets>
    <permissionSets>PS_OpportunityCreate</permissionSets>
    <permissionSets>PS_OpportunityEdit</permissionSets>
    <permissionSets>PS_OpportunityDelete</permissionSets>
    <mutingPermissionSets>MutePS_NoOpportunityDelete</mutingPermissionSets>
</PermissionSetGroup>
```

**Detection hint:** any output that produces two PSGs with overlapping `<permissionSets>` lists differing only by a single removed entry. The checker flags this as a consolidation candidate.

---

## Anti-Pattern 2: Including a grant PS and a mute together expecting them to cancel out

**What the LLM generates:**

```xml
<PermissionSetGroup>
    <permissionSets>PS_GrantOpportunityDelete</permissionSets>
    <mutingPermissionSets>MutePS_NoOpportunityDelete</mutingPermissionSets>
    <permissionSets>PS_AlsoGrantsOpportunityDelete</permissionSets>
</PermissionSetGroup>
```

…with commentary like "the second grant will override the mute."

**Why it happens:** The LLM applies symmetric "last write wins" thinking from layered configuration systems. Mute is asymmetric — it always wins over grants in the same PSG.

**Correct pattern:** if the persona genuinely needs Delete, do not include the mute. If only some users in the persona need Delete, build a different PSG without the mute and assign accordingly. There is no in-PSG override.

**Detection hint:** any PSG XML that lists both a `<permissionSets>` known to grant a permission AND a `<mutingPermissionSets>` known to subtract that same permission. The skill checker does not currently parse mute contents (an extension), but the human review should catch it.

---

## Anti-Pattern 3: Treating PSG recalculation as instantaneous

**What the LLM generates:**

```apex
// Generated automation
update permissionSetGroupToRecalc;
// Immediately assign users — assumes effective access is live.
insert new PermissionSetAssignment(
    AssigneeId = userId,
    PermissionSetGroupId = psgId
);
// Immediately query the user's permissions and act on them.
```

**Why it happens:** The LLM treats Salesforce metadata changes as synchronous, the way a database `UPDATE` is. PSG recalculation is asynchronous and `Status` reports the lifecycle.

**Correct pattern:**

```apex
// Wait for recalc before assuming new permissions are live.
PermissionSetGroup psg = [
    SELECT Id, Status FROM PermissionSetGroup WHERE Id = :psgId
];
if (psg.Status != 'Updated') {
    // Defer downstream work — re-queue, return early, or wait.
    return;
}
// Safe to act on effective access now.
```

**Detection hint:** any code path that updates a PSG (or a PS referenced by a PSG) and immediately makes decisions based on user permissions without checking `PermissionSetGroup.Status`.

---

## Anti-Pattern 4: Single-transaction destructive deployment of a PS still referenced by a PSG

**What the LLM generates:**

```text
"I'll create one deployment that:
  1. Updates PSG_A, PSG_B, PSG_C to remove PS_LegacyKnowledge.
  2. Deletes PS_LegacyKnowledge.
This will be one atomic change."
```

**Why it happens:** The LLM optimises for "one deployment" and treats the change as a transactional rename. Salesforce's recalculation does not release the FK-style reference within a single deployment window, so the delete fails.

**Correct pattern:** two deployments with a wait between them.

```text
1. Deploy PSG updates (remove PS_LegacyKnowledge from each PSG's permissionSets).
2. Poll: SELECT Id, DeveloperName, Status FROM PermissionSetGroup
         WHERE DeveloperName IN ('PSG_A', 'PSG_B', 'PSG_C')
   Wait until every row reports Status = 'Updated'.
3. Deploy the destructive change that deletes PS_LegacyKnowledge.
```

**Detection hint:** any destructive change set where `destructiveChanges.xml` lists a `PermissionSet` AND `package.xml` updates a `PermissionSetGroup` referencing that PS in the same deployment.

---

## Anti-Pattern 5: Re-implementing `ExpirationDate` as a scheduled Flow

**What the LLM generates:**

```text
"To time-box the contractor's access, I'll create a scheduled Flow that runs
nightly, queries PermissionSetAssignment rows tagged with a custom field, and
deletes them when the date is in the past."
```

**Why it happens:** The LLM treats expiration as a domain concern rather than a platform primitive, and reaches for Flow because Flow is the generic "scheduled action" tool.

**Correct pattern:** set `ExpirationDate` on the `PermissionSetAssignment` row directly. Salesforce auto-expires it and Setup Audit Trail records the event.

```apex
insert new PermissionSetAssignment(
    AssigneeId           = contractorUserId,
    PermissionSetGroupId = refundApproverPsgId,
    ExpirationDate       = Date.today().addDays(90)
);
```

**Detection hint:** any generated Flow named "Expire*Permission*", "Revoke*Access*", or similar that operates on `PermissionSetAssignment` records based on a date field. Replace with the platform primitive.

---

## Anti-Pattern 6: Forgetting to retrieve `MutingPermissionSet` alongside `PermissionSetGroup`

**What the LLM generates:**

```xml
<!-- package.xml for retrieving PSGs -->
<types>
    <members>*</members>
    <name>PermissionSetGroup</name>
</types>
<types>
    <members>*</members>
    <name>PermissionSet</name>
</types>
<!-- MutingPermissionSet missing -->
```

**Why it happens:** The LLM assumes the muting permission set is embedded inside the PSG metadata file. It is not — it is a separate `MutingPermissionSet` metadata type.

**Correct pattern:**

```xml
<types>
    <members>*</members>
    <name>PermissionSetGroup</name>
</types>
<types>
    <members>*</members>
    <name>PermissionSet</name>
</types>
<types>
    <members>*</members>
    <name>MutingPermissionSet</name>
</types>
```

**Detection hint:** any `package.xml` that includes `PermissionSetGroup` but not `MutingPermissionSet`. If the org uses mutes, the manifest is incomplete.

---

## Anti-Pattern 7: Naming PSGs after individuals, projects, or one-off exceptions

**What the LLM generates:**

```text
PSG_Janes_Custom_Bundle
PSG_Q4_Migration_Project
PSG_Refund_Hotfix_Sept_2025
```

**Why it happens:** The LLM picks the most specific, distinguishing string from the request. Short-term clarity, long-term debt — these PSGs survive the context that named them and become unintelligible.

**Correct pattern:** `PSG_<persona>_<env>` where persona is a stable role name and env is `Dev` / `UAT` / `Prod`.

```text
PSG_RefundApprover_Prod
PSG_ServiceLead_Prod
PSG_DataMigrationOperator_UAT
```

**Detection hint:** any PSG name that contains a person's name, a quarter or year, a project code, or the word "Hotfix" / "Temp" / "Custom". The skill checker flags PSG names that do not match the convention.

---

## Anti-Pattern 8: Auto-generating a PSG per profile during a profile-to-PSG migration

**What the LLM generates:** walks the profile list and produces one PSG per profile, each one a flat translation of every profile permission into included PSes — instant 60-PSG explosion, no composition.

**Why it happens:** "Migrate profiles to PSGs" reads like a 1:1 translation task. It is not — the migration is also a *consolidation* task, where many similar profiles collapse onto a smaller set of PSGs differentiated by mutes and small additive PSes.

**Correct pattern:** cluster the profiles by their actual permission overlap, build small composable PSes for each unique capability, and define PSGs per persona — typically 5–15 PSGs cover a 30-profile org. See `admin/permission-set-architecture` for the strategic side of this migration.

**Detection hint:** any output where the count of new PSGs equals or exceeds the count of source profiles. That is translation, not migration.
