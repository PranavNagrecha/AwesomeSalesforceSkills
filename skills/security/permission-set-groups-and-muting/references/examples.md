# Examples - Permission Set Groups And Muting

## Example 1: Shared Service Bundle With Muted Delete

**Context:** Senior and junior service agents need almost the same case access, but only seniors may delete cases or change `Case.Priority`.

**Problem:** Teams consider cloning two almost-identical permission sets and keeping them in sync forever.

**Solution:** Keep one permission set, build two groups over it, and give the junior group a muting permission set that enables (and so mutes) the two restricted permissions. The full files are in [metadata-examples.md](metadata-examples.md).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: force-app/main/default/mutingpermissionsets/Case_Agent_Junior_Muted.mutingpermissionset-meta.xml -->
<MutingPermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Case Agent Junior Muted</label>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>false</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Case</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</MutingPermissionSet>
```

Before relying on the mute, the team confirms that neither the agent profile nor any directly assigned permission set grants Case delete, because muting acts only inside the group.

**Why it works:** The model reuses the common bundle instead of multiplying near-duplicate permission sets, and the one difference is written down in one place.

---

## Example 2: Profile-Minimization Migration

**Context:** An org has many profiles with embedded feature permissions and frequent access drift.

**Problem:** Every change touches profiles and is hard to reason about. Profile grants also defeat muting.

**Solution:** Move feature-level permissions into focused permission sets, compose PSGs by persona, assign them alongside the old profiles, verify each persona with a real login once `PermissionSetGroup.Status` is `Updated`, then strip the feature permissions from the profiles in batches.

| Phase | Users | Profile grants | PSG assignment | Exit check |
|---|---|---|---|---|
| Pilot | 10 agents | unchanged | Case Agent Senior / Junior | Personas pass the access test script |
| Parallel run | one team | unchanged | all team members | No access tickets for two weeks |
| Profile reduction | one team | Case object permissions removed | unchanged | Junior agents can't delete cases |
| Cutover | all | minimal base profile | all personas | Access review signed off |

**Why it works:** Access becomes modular and auditable, and muting starts to work because the profile no longer grants the muted permissions.

---

## Anti-Pattern: PSG As A Junk Drawer

**What practitioners do:** They keep adding unrelated permission sets into one PSG because it is convenient.

**What goes wrong:** Access review and muting logic both become confusing, and a single muting set has to carry unrelated subtractions.

**Correct approach:** Keep permission sets and PSGs coherent and named for real bundles.
