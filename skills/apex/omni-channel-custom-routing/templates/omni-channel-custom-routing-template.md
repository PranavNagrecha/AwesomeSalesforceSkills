# Omni-Channel Custom Routing — Work Template

Use this template when implementing or reviewing Apex-driven skills-based routing via `PendingServiceRouting` and `SkillRequirement`.

## Scope

**Skill:** `omni-channel-custom-routing`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Omni-Channel / Skills-Based Routing enabled?** Yes / No
- **ServiceChannel DeveloperName(s):** (e.g. `Cases`, `Chat`)
- **Required Skill DeveloperName(s) and minimum levels:**
  - Skill: ___ — Level: ___  — Required (IsAdditionalSkill = false)
  - Skill: ___ — Level: ___  — Overflow (IsAdditionalSkill = true)
- **Work item SObject type:** (e.g. Case, LiveChatTranscript, custom object)
- **Routing trigger:** After-insert trigger / Batch job / Platform event handler
- **Overflow / relaxation needed?** Yes / No — timeout configured: ___ seconds
- **Known constraints:** (governor limits, record volume per transaction, etc.)

## Approach

Which pattern from SKILL.md applies?

- [ ] Bulk skills-based routing from trigger (single-transaction, after-insert)
- [ ] Batch-based routing with orphan cleanup
- [ ] Overflow routing with skill relaxation (IsAdditionalSkill = true)
- [ ] Other: ___

**Why this pattern:** (explain why the above pattern fits the requirement)

## Three-DML Sequence Checklist

Verify the implementation follows the mandatory sequence before marking complete:

- [ ] Step 1: `PendingServiceRouting` inserted with `IsReadyForRouting = false` and `RoutingType = 'SkillsBased'`
- [ ] Step 2: `SkillRequirement` records inserted with valid `RelatedRecordId` (populated after Step 1 insert)
- [ ] Step 3: `PendingServiceRouting` updated with `IsReadyForRouting = true`

## Quality Checklist

- [ ] `ServiceChannelId` resolved by querying `DeveloperName` at runtime — no hardcoded Id
- [ ] `Skill` Ids resolved by a single bulk SOQL query before any loops
- [ ] `Map<String, Id>` used for O(1) skill lookups inside processing loops
- [ ] Overflow skills marked `IsAdditionalSkill = true` (or confirmed not needed)
- [ ] `try/catch` wraps the full three-DML sequence
- [ ] `catch` block deletes any successfully-inserted `PendingServiceRouting` records on failure
- [ ] No `PendingServiceRouting` constructor sets `IsReadyForRouting = true`
- [ ] Tested in a sandbox with a live agent who has matching skills assigned in Omni-Channel

## Apex Scaffold

```apex
// 1. Resolve Ids — query once, outside any loops
Map<String, Id> channelMap = new Map<String, Id>();
for (ServiceChannel sc : [SELECT Id, DeveloperName FROM ServiceChannel
                           WHERE DeveloperName IN :requiredChannelNames]) {
    channelMap.put(sc.DeveloperName, sc.Id);
}

Map<String, Id> skillMap = new Map<String, Id>();
for (Skill s : [SELECT Id, DeveloperName FROM Skill
                WHERE DeveloperName IN :requiredSkillNames]) {
    skillMap.put(s.DeveloperName, s.Id);
}

// 2. DML 1 — Insert PendingServiceRouting (flag = false)
List<PendingServiceRouting> psrList = new List<PendingServiceRouting>();
for (SObject workItem : workItems) {
    psrList.add(new PendingServiceRouting(
        WorkItemId        = workItem.Id,
        ServiceChannelId  = channelMap.get('YourChannelDeveloperName'),
        RoutingType       = 'SkillsBased',
        IsReadyForRouting = false,
        RoutingPriority   = 1,
        CapacityWeight    = 1
    ));
}
List<PendingServiceRouting> insertedPsrs = new List<PendingServiceRouting>();
try {
    insert psrList;
    insertedPsrs.addAll(psrList);

    // 3. DML 2 — Insert SkillRequirement records
    List<SkillRequirement> srList = new List<SkillRequirement>();
    for (PendingServiceRouting psr : psrList) {
        srList.add(new SkillRequirement(
            RelatedRecordId   = psr.Id,
            SkillId           = skillMap.get('RequiredSkillDeveloperName'),
            SkillLevel        = 3,          // minimum proficiency (1–10)
            IsAdditionalSkill = false       // required skill
        ));
        srList.add(new SkillRequirement(
            RelatedRecordId   = psr.Id,
            SkillId           = skillMap.get('OverflowSkillDeveloperName'),
            SkillLevel        = 1,
            IsAdditionalSkill = true        // dropped after relaxation timeout
        ));
    }
    insert srList;

    // 4. DML 3 — Flip IsReadyForRouting = true
    for (PendingServiceRouting psr : psrList) {
        psr.IsReadyForRouting = true;
    }
    update psrList;

} catch (Exception ex) {
    // Clean up orphaned PendingServiceRouting records to prevent DUPLICATE_VALUE
    if (!insertedPsrs.isEmpty()) {
        delete insertedPsrs;
    }
    // Log or re-throw as appropriate
    throw ex;
}
```

## Notes

Record any deviations from the standard pattern and why.

- Deviation: ___
- Reason: ___
