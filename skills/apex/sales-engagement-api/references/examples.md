# Examples — Sales Engagement API

## Example 1: Bulk Cadence Enrollment from a Trigger or Batch Job

**Context:** A nightly batch job identifies newly qualified Leads and must enroll each one in a specific Sales Engagement cadence. The batch processes up to 200 records per chunk.

**Problem:** Developers unfamiliar with the Sales Engagement API attempt to insert `ActionCadenceTracker` records directly or call the invocable action one record at a time inside a loop, hitting governor limits and producing silent failures when duplicates exist.

**Solution:**

```apex
public class CadenceEnrollmentService {

    public static final String CADENCE_NAME = 'New Lead Outreach Q2';

    /**
     * Enroll a list of Lead or Contact IDs into the specified cadence.
     * Caller must pass the assigned rep's User ID.
     * Returns a map of targetId -> error message for failed enrollments.
     */
    public static Map<Id, String> enrollTargets(
        List<Id> targetIds,
        String cadenceName,
        Id assignedUserId
    ) {
        Map<Id, String> errorsByTarget = new Map<Id, String>();

        // Guard: skip any targets already in an active enrollment
        Set<Id> alreadyEnrolled = getActivelyEnrolledIds(targetIds);
        List<Id> toEnroll = new List<Id>();
        for (Id tid : targetIds) {
            if (!alreadyEnrolled.contains(tid)) {
                toEnroll.add(tid);
            }
        }

        if (toEnroll.isEmpty()) {
            return errorsByTarget;
        }

        // Build bulk inputs — one per target
        List<Invocable.Action.Input> inputs = new List<Invocable.Action.Input>();
        for (Id tid : toEnroll) {
            Invocable.Action.Input inp = new Invocable.Action.Input();
            inp.put('targetId', tid);
            inp.put('cadenceName', cadenceName);
            inp.put('userId', assignedUserId);
            // sObjectName is required; derive from ID prefix
            inp.put('sObjectName', tid.getSObjectType().getDescribe().getName());
            inputs.add(inp);
        }

        // Invoke in bulk
        List<Invocable.Action.Result> results =
            Invocable.Action.createCustomAction('apex', 'assignTargetToSalesCadence')
                .invoke(inputs);

        // Inspect each result — do not assume success
        for (Integer i = 0; i < results.size(); i++) {
            Invocable.Action.Result r = results[i];
            if (!r.isSuccess()) {
                Id tid = toEnroll[i];
                List<String> msgs = new List<String>();
                for (Invocable.Action.Error e : r.getErrors()) {
                    msgs.add(e.getMessage());
                }
                errorsByTarget.put(tid, String.join(msgs, '; '));
            }
        }

        return errorsByTarget;
    }

    private static Set<Id> getActivelyEnrolledIds(List<Id> targetIds) {
        Set<Id> enrolled = new Set<Id>();
        for (ActionCadenceTracker act : [
            SELECT TargetId
            FROM ActionCadenceTracker
            WHERE TargetId IN :targetIds
              AND State = 'Active'
        ]) {
            enrolled.add(act.TargetId);
        }
        return enrolled;
    }
}
```

**Why it works:** Building a list of `Invocable.Action.Input` objects and calling `invoke` once for all targets keeps DML and CPU consumption flat regardless of list size. Inspecting each `Invocable.Action.Result` ensures per-record errors (duplicate enrollment, license issue, missing cadence) are captured rather than swallowed. The pre-flight SOQL guard removes already-enrolled targets before the action call, avoiding the silent no-op on duplicate enrollment.

---

## Example 2: CDC Async Apex Trigger for Enrollment Lifecycle Reactions

**Context:** When a prospect's cadence run completes (all steps finished or manually paused), a downstream process must update a custom Lead scoring field and notify a Slack channel. Triggers on `ActionCadenceTracker` are not supported, so a CDC-based subscriber is required.

**Problem:** Developers attempt to write a standard Apex trigger on `ActionCadenceTracker` or poll with a scheduled job. The trigger fails to deploy. The polling job misses rapid state transitions and uses excessive SOQL queries per execution.

**Solution:**

First, enable CDC on `ActionCadenceTracker` in Setup > Integrations > Change Data Capture, then add the object to the Selected Entities list.

```apex
// Async Apex Trigger on the CDC change event channel
trigger ActionCadenceTrackerCDC on ActionCadenceTrackerChangeEvent (after insert) {
    List<ActionCadenceTrackerChangeEvent> events = Trigger.new;

    // Collect relevant tracker IDs for state changes worth acting on
    List<Id> completedTrackerIds = new List<Id>();

    for (ActionCadenceTrackerChangeEvent evt : events) {
        EventBus.ChangeEventHeader header = evt.ChangeEventHeader;

        // Only react to UPDATE operations where State changed
        if (header.changeType != 'UPDATE') {
            continue;
        }

        // changedFields contains the API names of fields that changed
        if (!header.changedFields.contains('State')) {
            continue;
        }

        // State == 'Complete' or 'Paused' signals an actionable transition
        if (evt.State == 'Complete' || evt.State == 'Paused') {
            for (String recId : header.recordIds) {
                completedTrackerIds.add((Id) recId);
            }
        }
    }

    if (!completedTrackerIds.isEmpty()) {
        // Hand off to Queueable for callout + DML work
        System.enqueueJob(new CadenceCompletionWorker(completedTrackerIds));
    }

    // Acknowledge checkpoint for reliable delivery
    EventBus.TriggerContext.currentContext().setResumeCheckpoint(
        events[events.size() - 1].ReplayId
    );
}
```

```apex
public class CadenceCompletionWorker implements Queueable, Database.AllowsCallouts {

    private List<Id> trackerIds;

    public CadenceCompletionWorker(List<Id> trackerIds) {
        this.trackerIds = trackerIds;
    }

    public void execute(QueueableContext ctx) {
        // Query enriched data from the tracker records
        List<ActionCadenceTracker> trackers = [
            SELECT Id, TargetId, State, ActionCadenceId
            FROM ActionCadenceTracker
            WHERE Id IN :trackerIds
        ];

        // Update custom scoring fields, send notifications, etc.
        List<Lead> leadsToUpdate = new List<Lead>();
        for (ActionCadenceTracker t : trackers) {
            if (t.TargetId.getSObjectType() == Schema.Lead.SObjectType) {
                leadsToUpdate.add(new Lead(
                    Id = t.TargetId,
                    Cadence_Complete__c = true,
                    Last_Cadence_State__c = t.State
                ));
            }
        }

        if (!leadsToUpdate.isEmpty()) {
            update leadsToUpdate;
        }

        // Callout to Slack or other external system follows here
    }
}
```

**Why it works:** The Async Apex Trigger subscribes to `ActionCadenceTrackerChangeEvent` — the only supported mechanism for reacting to tracker state changes from Apex. Setting the resume checkpoint ensures the event bus resumes delivery from the correct position if the trigger fails. Delegating to Queueable separates CDC event processing (fast, no DML or callout) from the downstream work that needs both.

---

## Anti-Pattern: Inserting ActionCadenceTracker Records Directly

**What practitioners do:** Attempt to enroll a lead by constructing and inserting an `ActionCadenceTracker` object directly, treating it like a junction object.

```apex
// WRONG — do not do this
ActionCadenceTracker tracker = new ActionCadenceTracker();
tracker.TargetId = leadId;
tracker.ActionCadenceId = cadenceId;
insert tracker; // will throw a DmlException
```

**What goes wrong:** The platform rejects the DML operation. `ActionCadenceTracker` is a system-managed object. The Sales Engagement engine enforces enrollment rules (license checks, duplicate prevention, step scheduling) inside the `assignTargetToSalesCadence` invocable action. Bypassing it is not possible.

**Correct approach:** Use `Invocable.Action` to call `assignTargetToSalesCadence` with the required inputs as shown in Example 1. Inspect the result for errors per record.
