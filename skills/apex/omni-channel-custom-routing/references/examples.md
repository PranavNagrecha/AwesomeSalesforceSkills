# Examples — Omni-Channel Custom Routing

## Example 1: Bulk Skills-Based Routing from a Case After-Insert Trigger

**Context:** A service team routes new Cases to agents based on two skills: a required product skill and an optional language skill for overflow. The trigger fires on Case insert and must handle batches of up to 200 records.

**Problem:** Without bulkification, SOQL queries for `ServiceChannel` and `Skill` inside the record loop exhaust governor limits on any meaningful volume. Additionally, setting `IsReadyForRouting = true` on the initial insert (before `SkillRequirement` records exist) causes the routing engine to evaluate the work item with zero requirements.

**Solution:**

```apex
trigger CaseCustomRouting on Case (after insert) {
    // Step 1: Collect all DeveloperNames needed — query once outside the loop
    Set<String> channelNames = new Set<String>{ 'Cases' };
    Set<String> skillNames   = new Set<String>{ 'Product_Support', 'Spanish_Language' };

    Map<String, Id> channelByDevName = new Map<String, Id>();
    for (ServiceChannel sc : [
        SELECT Id, DeveloperName
        FROM ServiceChannel
        WHERE DeveloperName IN :channelNames
    ]) {
        channelByDevName.put(sc.DeveloperName, sc.Id);
    }

    Map<String, Id> skillByDevName = new Map<String, Id>();
    for (Skill s : [
        SELECT Id, DeveloperName
        FROM Skill
        WHERE DeveloperName IN :skillNames
    ]) {
        skillByDevName.put(s.DeveloperName, s.Id);
    }

    Id caseChannelId  = channelByDevName.get('Cases');
    Id productSkillId = skillByDevName.get('Product_Support');
    Id languageSkillId = skillByDevName.get('Spanish_Language');

    if (caseChannelId == null || productSkillId == null) {
        // Log and exit — required configuration missing
        System.debug(LoggingLevel.ERROR,
            'CaseCustomRouting: Missing ServiceChannel or Skill configuration.');
        return;
    }

    // Step 2: Insert PendingServiceRouting with IsReadyForRouting = FALSE
    List<PendingServiceRouting> psrList = new List<PendingServiceRouting>();
    for (Case c : Trigger.new) {
        PendingServiceRouting psr = new PendingServiceRouting(
            WorkItemId        = c.Id,
            ServiceChannelId  = caseChannelId,
            RoutingType       = 'SkillsBased',
            IsReadyForRouting = false,
            RoutingPriority   = 1,
            CapacityWeight    = 1
        );
        psrList.add(psr);
    }
    insert psrList;

    // Step 3: Insert SkillRequirement records linked to each PendingServiceRouting
    List<SkillRequirement> srList = new List<SkillRequirement>();
    for (PendingServiceRouting psr : psrList) {
        // Required skill — must be matched
        srList.add(new SkillRequirement(
            RelatedRecordId  = psr.Id,
            SkillId          = productSkillId,
            SkillLevel       = 3,
            IsAdditionalSkill = false
        ));
        // Optional (overflow) skill — dropped after relaxation timeout
        if (languageSkillId != null) {
            srList.add(new SkillRequirement(
                RelatedRecordId  = psr.Id,
                SkillId          = languageSkillId,
                SkillLevel       = 1,
                IsAdditionalSkill = true
            ));
        }
    }
    insert srList;

    // Step 4: Flip IsReadyForRouting = TRUE — activates the routing engine
    for (PendingServiceRouting psr : psrList) {
        psr.IsReadyForRouting = true;
    }
    update psrList;
}
```

**Why it works:** The three DML operations occur in the mandatory sequence. `ServiceChannel` and `Skill` Ids are resolved once per transaction via bulk SOQL — no per-record queries. The language skill is marked `IsAdditionalSkill = true` so the platform drops it automatically after the configured timeout if no bilingual agent is available, falling back to any agent with the product skill.

---

## Example 2: Error-Safe Routing with Orphan Cleanup

**Context:** A scheduled batch job routes unrouted Cases. An error mid-sequence could leave orphaned `PendingServiceRouting` records that block future routing attempts for the same work items.

**Problem:** If the `SkillRequirement` insert or the `IsReadyForRouting` update fails after the `PendingServiceRouting` insert already succeeded, the work item is stuck with an orphaned routing record. Subsequent routing attempts fail with a DUPLICATE_VALUE error because only one active `PendingServiceRouting` is allowed per work item.

**Solution:**

```apex
public class CaseRoutingBatch implements Database.Batchable<SObject> {

    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return Database.getQueryLocator(
            'SELECT Id FROM Case WHERE Status = \'New\' AND OwnerId = :queueId'
        );
    }

    public void execute(Database.BatchableContext ctx, List<Case> scope) {
        // Resolve Ids once per batch chunk
        Map<String, Id> channelMap = getChannelMap(new Set<String>{ 'Cases' });
        Map<String, Id> skillMap   = getSkillMap(
            new Set<String>{ 'Technical_Support', 'Enterprise_Tier' }
        );

        Id channelId = channelMap.get('Cases');
        Id techSkillId = channelMap.get('Technical_Support');  // intentional: will be null, shows guard
        techSkillId    = skillMap.get('Technical_Support');
        Id tierSkillId = skillMap.get('Enterprise_Tier');

        if (channelId == null || techSkillId == null) { return; }

        List<PendingServiceRouting> insertedPsrs = new List<PendingServiceRouting>();
        try {
            // DML 1: Insert PSRs with flag = false
            List<PendingServiceRouting> psrList = new List<PendingServiceRouting>();
            for (Case c : scope) {
                psrList.add(new PendingServiceRouting(
                    WorkItemId        = c.Id,
                    ServiceChannelId  = channelId,
                    RoutingType       = 'SkillsBased',
                    IsReadyForRouting = false,
                    RoutingPriority   = 1,
                    CapacityWeight    = 1
                ));
            }
            insert psrList;
            insertedPsrs.addAll(psrList);

            // DML 2: Insert SkillRequirements
            List<SkillRequirement> srList = new List<SkillRequirement>();
            for (PendingServiceRouting psr : psrList) {
                srList.add(new SkillRequirement(
                    RelatedRecordId   = psr.Id,
                    SkillId           = techSkillId,
                    SkillLevel        = 2,
                    IsAdditionalSkill = false
                ));
                if (tierSkillId != null) {
                    srList.add(new SkillRequirement(
                        RelatedRecordId   = psr.Id,
                        SkillId           = tierSkillId,
                        SkillLevel        = 1,
                        IsAdditionalSkill = true
                    ));
                }
            }
            insert srList;

            // DML 3: Flip IsReadyForRouting = true
            for (PendingServiceRouting psr : psrList) {
                psr.IsReadyForRouting = true;
            }
            update psrList;

        } catch (Exception ex) {
            // Clean up orphaned PSRs to prevent DUPLICATE_VALUE on next attempt
            if (!insertedPsrs.isEmpty()) {
                try {
                    delete insertedPsrs;
                } catch (Exception cleanupEx) {
                    System.debug(LoggingLevel.ERROR,
                        'CaseRoutingBatch cleanup failed: ' + cleanupEx.getMessage());
                }
            }
            System.debug(LoggingLevel.ERROR,
                'CaseRoutingBatch routing failed: ' + ex.getMessage());
        }
    }

    public void finish(Database.BatchableContext ctx) {}

    private Map<String, Id> getChannelMap(Set<String> devNames) {
        Map<String, Id> result = new Map<String, Id>();
        for (ServiceChannel sc : [
            SELECT Id, DeveloperName FROM ServiceChannel WHERE DeveloperName IN :devNames
        ]) {
            result.put(sc.DeveloperName, sc.Id);
        }
        return result;
    }

    private Map<String, Id> getSkillMap(Set<String> devNames) {
        Map<String, Id> result = new Map<String, Id>();
        for (Skill s : [
            SELECT Id, DeveloperName FROM Skill WHERE DeveloperName IN :devNames
        ]) {
            result.put(s.DeveloperName, s.Id);
        }
        return result;
    }
}
```

**Why it works:** The `try/catch` block catches any failure mid-sequence and deletes any `PendingServiceRouting` records that were already inserted, preventing orphans. The batch size is bounded by the default 200-record chunk, keeping DML counts well within governor limits.

---

## Anti-Pattern: Setting IsReadyForRouting = true on Insert

**What practitioners do:** To simplify the code, some implementations set `IsReadyForRouting = true` during the initial `PendingServiceRouting` insert, relying on the assumption that the routing engine will wait for `SkillRequirement` records.

**What goes wrong:** The routing engine evaluates the work item immediately when `IsReadyForRouting = true` is set. If `SkillRequirement` records have not yet been inserted, the engine sees zero skill requirements and may route to any available agent — ignoring skill matching entirely. In some configurations this raises a DML exception instead.

**Correct approach:** Always insert `PendingServiceRouting` with `IsReadyForRouting = false`, insert all `SkillRequirement` records, then update `IsReadyForRouting` to `true` as the final step.
