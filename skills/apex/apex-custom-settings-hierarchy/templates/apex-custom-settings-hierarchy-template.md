# Apex Custom Settings Hierarchy — Work Template

Use this template when creating or changing a Hierarchy Custom Setting and its Apex consumers.

## Scope

**Skill:** `apex-custom-settings-hierarchy`

**Request summary:** (fill in what the user asked for — new flag? migration? bug fix?)

## Classification Check

Before anything else, confirm this config belongs in a Hierarchy Custom Setting:

- [ ] Value must be **changed in production Setup UI** by admins.
- [ ] Needs **per-user, per-profile, or org-default** variation automatically.
- [ ] Change cadence is **minutes to hours**, not weeks.

If any of these are false, migrate to Custom Metadata Types.

## Context Gathered

- **Setting name / fields:**
- **Editors (roles/profiles):**
- **Callers:** (list classes/triggers that read it)
- **Change cadence:** (daily? per-incident?)
- **Audit needs:** (field history? SOX? none)
- **Privileged flag setting:** (true/false — justification)

## Approach

- [ ] Null-safe field read with explicit code default
- [ ] Batch upsert by `SetupOwnerId` (no DML in loops)
- [ ] Test covers all three tiers (org default, profile, user)
- [ ] Seeding procedure documented / automated

## Code Sketch

```apex
public with sharing class {{FlagAccessor}} {
    public static Boolean isEnabled() {
        {{Setting}}__c s = {{Setting}}__c.getInstance();
        return s != null && s.{{Field}}__c == true;
    }
}
```

## Checklist

- [ ] `getInstance()` used (not `getOrgDefaults()` unless justified).
- [ ] Field-level null check; code default for missing values.
- [ ] `Privileged` flag matches security posture.
- [ ] Tests seed each tier with `System.runAs` where relevant.
- [ ] Seeding procedure for production documented.
- [ ] No SOQL against the Custom Setting object.

## Notes

Record any deviations from the standard pattern and why. Especially call out any reason you picked Custom Settings over Custom Metadata.
