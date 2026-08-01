# LLM Anti-Patterns — Agent Security Review

Scope: the pre-production review of an agent's identity, access and audit surface.
Adversarial prompt testing is a different job and belongs to
`agentforce/prompt-injection-defense`; this file deliberately does not repeat it. The
question here is not "can the agent be talked into it" but "what could it reach if it
were".

## Anti-Pattern 1: Signing off an action class with no sharing declaration

Assistants generate `public class EscalateCaseAction { ... }` with no sharing keyword and
reviewers read the absence as harmless. It is not. An Apex class that omits the keyword
runs in the sharing context of its caller, and an invocable action is itself the entry
point to the transaction — so there is no caller to inherit restraint from. The class
that matters most is the one whose sharing is unstated.

**Wrong** — no keyword on an entry-point class, so record-level sharing is not enforced:

```apex
public class EscalateCaseAction {
    @InvocableMethod(label='Escalate Case')
    public static List<Response> run(List<Request> reqs) {
        List<Case> cases = [SELECT Id, OwnerId FROM Case WHERE Id IN :ids];
        ...
    }
}
```

**Right** — explicit sharing, with CRUD/FLS enforced separately from record sharing:

```apex
public with sharing class EscalateCaseAction {
    @InvocableMethod(label='Escalate Case')
    public static List<Response> run(List<Request> reqs) {
        List<Case> cases = [
            SELECT Id, OwnerId, Priority FROM Case WHERE Id IN :ids WITH USER_MODE
        ];
        ...
    }
}
```

Record the keyword for every action class in the review table. `inherited sharing` is a
legitimate answer for a shared helper, but the documented behaviour is that it runs as
`with sharing` when it is itself the entry point — so on an invocable class it is a
weaker way of writing `with sharing`, not a different one.

Source: Using the with sharing, without sharing, and inherited sharing Keywords —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm

## Anti-Pattern 2: Believing `with sharing` covers field-level security

The most consistent reviewer error. `with sharing` governs which *records* the user can
see. It says nothing about which *objects* and *fields* they may read or write, so a
`with sharing` class happily returns and writes a field the running user has no access
to.

❌ "The class is `with sharing`, so field access is enforced."
✅ Two independent controls, both checked in the review: sharing keyword for record
access, and `WITH USER_MODE` on queries or `Security.stripInaccessible` on results for
object and field access. A review row that records only the sharing keyword is
incomplete.

Source: Enforcing Object and Field Permissions —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm

## Anti-Pattern 3: Reviewing the run-as user's permission set and ignoring their profile

Assistants inspect the dedicated permission set, find it minimal, and pass the review.
Effective access is the union of the profile, every assigned permission set, every
permission set group, and any permission set licence — so a minimal permission set on a
Standard User profile can still carry broad access.

❌ Read `Agentforce_Service_Agent` permission set, conclude least privilege.
✅ Query effective access, and specifically look for the system permissions that make
sharing irrelevant:

```apex
Id agentUserId = [SELECT Id FROM User WHERE Username = 'svc.agent@example.com'].Id;
// Run this in anonymous Apex against the agent's run-as user.
for (PermissionSetAssignment psa : [
        SELECT PermissionSet.Name, PermissionSet.IsOwnedByProfile,
               PermissionSet.PermissionsViewAllData, PermissionSet.PermissionsModifyAllData,
               PermissionSet.PermissionsViewAllUsers, PermissionSet.PermissionsAuthorApex
        FROM PermissionSetAssignment WHERE AssigneeId = :agentUserId]) {
    System.debug(psa.PermissionSet.Name + ' VAD=' + psa.PermissionSet.PermissionsViewAllData
        + ' MAD=' + psa.PermissionSet.PermissionsModifyAllData);
}
```

`PermissionSet` rows where `IsOwnedByProfile = true` are the profile's permissions
surfaced as a permission set — which is why profile-granted **View All Data** shows up
here and nowhere in the permission-set list an admin would think to open. Any agent whose
effective access includes View All Data or Modify All Data has no meaningful record-level
boundary, and the rest of the review is decoration.

## Anti-Pattern 4: Generic record-write actions

Asked for "an action to update a case", assistants produce one that accepts a field name
and a value. Every field on the object becomes reachable, including `OwnerId`,
`RecordTypeId` and any approval or audit field, and no server-side rule can distinguish
a legitimate call from an abusive one because the action has no semantics.

❌ One `UpdateRecord(objectName, fieldName, value)` action.
✅ Named actions with fixed, reviewable write scope — `CloseCase`, `AddCaseComment`,
`EscalateCase` — each writing an explicit, short list of fields. The review artefact is
the union of those field lists; if a field is not on it, the agent cannot write it.

## Anti-Pattern 5: Reviewing the agent's access but not the grounding query's

Actions get scrutinised because they write. Grounding gets waved through because it only
reads — but grounding is what puts record content into the prompt, and a grounding
selector written without user-mode enforcement will return rows the end user has no right
to see, which the agent will then summarise back to them.

❌ Ground with a `without sharing` selector "so the agent always has context".
✅ Every grounding selector runs under the end user's access and selects a narrow,
enumerated field list. Test it by asking the agent, as a low-privilege user, about a
record owned by someone else and confirming it cannot answer.

## Anti-Pattern 6: Producing a document instead of a re-runnable artefact

The output is a slide deck. Six weeks later a new action ships, the run-as user gains a
permission set, and nothing re-checks either. Agent configuration drifts faster than the
review cadence.

❌ A signed PDF in a folder.
✅ A checklist whose rows are assertions something can execute — the sharing keyword per
action class, the effective-permission query above, the grounding field lists — stored
with the agent metadata so a change to either shows up as a diff.

## Anti-Pattern 7: No audit trail for the action layer

Assistants add logging to the conversation and consider the agent observable. The
security-relevant events are the ones on the platform side: who the action ran as, which
records it touched, and which configuration changed since the last review.

❌ Conversation transcripts only.
✅ Confirm in the review that `SetupAuditTrail` covers the configuration changes,
`EventLogFile` (`ApexExecution`, `API`, `ContentTransfer` event types) is being retrieved
and retained where the Event Monitoring entitlement exists, and each action writes its
own structured record — run-as user, reason code, record ids touched — so a forensic
question has an answer that is not "we would have to reproduce it".

Source: EventLogFile object reference —
https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventlogfile.htm
