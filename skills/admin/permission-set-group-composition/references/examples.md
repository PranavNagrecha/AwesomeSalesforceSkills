# Examples — Permission Set Group Composition

Three realistic composition scenarios that exercise the patterns and gotchas in `SKILL.md`.

---

## Example 1 — Sales-Rep PSG with a Manager mute variant

### Context

A Sales Cloud org has a "Sales Rep" persona with full Opportunity CRUD (read, create, edit, delete). The business now wants a "Sales Manager" persona that should have **everything Sales Rep has, except Delete on Opportunity** — managers should not be able to bulk-delete pipeline data.

### Wrong approach (cloning)

Admin clones `PSG_SalesRep_Prod` to `PSG_SalesManager_Prod`, opens the new PSG, and removes the PS that grants Delete. Six months later the Sales Rep bundle is updated to add `Forecasting_Edit` — and the manager bundle silently lags behind because nobody remembers the clone.

### Correct approach (mute)

```text
Permission Sets (small, composable):
- PS_OpportunityRead
- PS_OpportunityCreate
- PS_OpportunityEdit
- PS_OpportunityDelete
- PS_ForecastingEdit  (added later — both PSGs pick it up automatically)

Mute Permission Set:
- MutePS_NoOpportunityDelete
    object: Opportunity
    permission: Delete = false (mute)

PSGs:
- PSG_SalesRep_Prod
    permissionSets:
      - PS_OpportunityRead
      - PS_OpportunityCreate
      - PS_OpportunityEdit
      - PS_OpportunityDelete

- PSG_SalesManager_Prod
    permissionSets:
      - PS_OpportunityRead
      - PS_OpportunityCreate
      - PS_OpportunityEdit
      - PS_OpportunityDelete
    mutingPermissionSets:
      - MutePS_NoOpportunityDelete
```

### Why this works

The two PSGs share the same underlying PSes. When `PS_ForecastingEdit` is added to both, the change is symmetric. The manager-specific delta is one tiny mute file with a clear name, easy to audit, and nothing is duplicated.

### What the metadata looks like

`permissionsetgroups/PSG_SalesManager_Prod.permissionsetgroup-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSetGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Sales Manager — same as Rep, no Opportunity delete</description>
    <hasActivationRequired>false</hasActivationRequired>
    <permissionSets>PS_OpportunityRead</permissionSets>
    <permissionSets>PS_OpportunityCreate</permissionSets>
    <permissionSets>PS_OpportunityEdit</permissionSets>
    <permissionSets>PS_OpportunityDelete</permissionSets>
    <mutingPermissionSets>MutePS_NoOpportunityDelete</mutingPermissionSets>
</PermissionSetGroup>
```

`mutingpermissionsets/MutePS_NoOpportunityDelete.mutingpermissionset-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MutingPermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Subtract Delete on Opportunity from any PSG that includes it</description>
    <objectPermissions>
        <object>Opportunity</object>
        <allowDelete>false</allowDelete>
    </objectPermissions>
</MutingPermissionSet>
```

Note the muting permission set is its own metadata file, not embedded in the PSG. A `package.xml` for source-tracked deployment must list both `PermissionSetGroup` AND `MutingPermissionSet` types.

---

## Example 2 — Time-boxed elevation with an expired PSG assignment

### Context

A Service Cloud contractor needs Refund Approver rights for the duration of a 90-day support engagement. After day 90 the access must come off automatically — no admin should have to remember to revoke it.

### Wrong approach (custom Flow)

A scheduled Flow runs nightly, queries `PermissionSetAssignment` rows tagged with a custom field, and deletes them when the tag's date is in the past. The Flow fails silently in a test sandbox refresh, the contractor keeps Refund Approver access for an extra month, and the audit team finds it during quarterly review.

### Correct approach (`ExpirationDate` on the assignment)

Assign the existing `PSG_RefundApprover_Prod` to the contractor with an `ExpirationDate` set 90 days out. Salesforce auto-expires the assignment at midnight on that date and Setup Audit Trail records the expiration event.

```apex
// One-off setup script — could equally be done in the Permission Set Group assignment UI.
PermissionSetAssignment psa = new PermissionSetAssignment(
    AssigneeId           = '005XX000001ContractorId',
    PermissionSetGroupId = '0PGXX0000004RefundApproverGroupId',
    ExpirationDate       = Date.today().addDays(90)
);
insert psa;
```

After day 90, querying `[SELECT Id, IsActive, ExpirationDate FROM PermissionSetAssignment WHERE Id = :psa.Id]` shows `IsActive = false` and the user no longer has Refund Approver effective access.

### Why this works

Expiration is a platform primitive — no custom code, no scheduled job, no silent failure mode. Setup Audit Trail captures both the original assignment (with the expiration date) and the auto-expiration event.

---

## Example 3 — PSG deletion blocked by a still-referenced PS

### Context

The team is retiring `PS_LegacyKnowledge` because Knowledge has been migrated to Lightning. The PS is referenced by three PSGs (`PSG_SupportAgent_Prod`, `PSG_SupportLead_Prod`, `PSG_KnowledgePublisher_Prod`).

### Wrong approach (single-deployment delete)

A developer creates a deployment that updates the three PSGs to drop the reference AND deletes `PS_LegacyKnowledge` in the same change-set. The deployment fails with:

```
DEPLOY FAILED: PermissionSet PS_LegacyKnowledge cannot be deleted because it is
referenced by one or more Permission Set Groups. Remove the reference and wait
for recalculation to complete before deleting.
```

The PSG updates landed, but the recalc was still running when the delete fired, so the FK reference was still live in Salesforce's recalculation cache. The whole deployment rolls back.

### Correct approach (detach → wait → delete)

**Deployment 1 — detach:** Remove `PS_LegacyKnowledge` from each of the three PSG metadata files and deploy.

```diff
 <PermissionSetGroup>
     <permissionSets>PS_KnowledgeRead</permissionSets>
-    <permissionSets>PS_LegacyKnowledge</permissionSets>
     <permissionSets>PS_CaseConsole</permissionSets>
 </PermissionSetGroup>
```

**Wait — verify recalculation:** Poll the three PSGs until each reports `Status = Updated`. Anonymous Apex check:

```apex
List<PermissionSetGroup> groups = [
    SELECT Id, DeveloperName, Status
    FROM PermissionSetGroup
    WHERE DeveloperName IN (
        'PSG_SupportAgent_Prod',
        'PSG_SupportLead_Prod',
        'PSG_KnowledgePublisher_Prod'
    )
];
for (PermissionSetGroup g : groups) {
    System.debug(g.DeveloperName + ' -> ' + g.Status);
}
// Expect: all three -> Updated.  Outdated/Updating means wait.
```

If any PSG is `Outdated` or `Updating`, kick recalc explicitly via the `recalculate` REST endpoint or wait. Do not proceed until all three are `Updated`.

**Deployment 2 — delete:** Now deploy the destructive change that removes `PS_LegacyKnowledge.permissionset-meta.xml`. The deployment succeeds because no PSG holds a reference.

### Why this works

The recalculation lifecycle is asynchronous; treating it as instantaneous is the bug. Splitting the change into two deployments with an explicit wait between them respects the platform's actual semantics.

---

## Anti-Pattern: Cloning a PSG to make a small variant

**What practitioners do:** A new persona is "almost like Sales Rep but without one permission." The admin clones `PSG_SalesRep_Prod` to `PSG_SalesRepNoExport_Prod` and edits the clone.

**What goes wrong:** Two PSGs now reference the same big pile of PSes. Any edit to the rep bundle has to be re-applied to the clone, manually, every time. Six months in, the two PSGs have drifted in three places and the audit team cannot tell which permissions are intentional and which are stale.

**Correct approach:** One PSG `PSG_SalesRep_Prod`. One Mute Permission Set `MutePS_NoExport`. One PSG `PSG_SalesRepNoExport_Prod` that includes the same PSes plus the mute. Future edits to the rep bundle propagate automatically; the variant is documented in one tiny mute file.

---

## Anti-Pattern: Muting a permission then re-granting it via another PS in the same PSG

**What practitioners do:** A PSG includes `PS_A` (grants Delete on Opportunity) and `MutePS_NoOpportunityDelete` (mutes Delete on Opportunity). The admin then adds `PS_B` (also grants Delete on Opportunity) hoping it overrides the mute.

**What goes wrong:** The user still does not get Delete on Opportunity. Mute is one-way subtract — once mute is applied, no included PS in the same PSG can grant the muted permission back. The admin spends an afternoon hunting for the "rule" that is suppressing the access; the rule is the mute, working as documented.

**Correct approach:** If the persona genuinely needs Delete on Opportunity, do not include the mute. If only some users in the persona need it, build a second PSG without the mute and assign accordingly.
