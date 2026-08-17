# LLM Anti-Patterns — Permission Set Expiration

Common mistakes AI coding assistants make when generating or advising on time-boxed permission set access.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Building a Scheduled Job Instead of Using `ExpirationDate`

**What the LLM generates:** A scheduled Flow or a `Schedulable` Apex class that runs nightly, queries `PermissionSetAssignment` for rows past a custom `Access_End_Date__c` field, and deletes them. Often accompanied by a custom object to hold the elevation requests and a custom field on User.

**Why it happens:** "Revoke access after N days" is a recognisable software problem with a recognisable software answer, and cron-shaped solutions dominate training data. The model does not reach for a platform field it associates with nothing memorable.

**Why it is wrong:** it duplicates a platform primitive, and it swaps a mechanism with no failure path for one that fails silently. A scheduled job that errors, hits a limit, or is deactivated during a deployment leaves standing privilege in place and tells nobody — the precise outcome the control exists to prevent. It also has to model the Create-only fields correctly to do a re-grant, which most generated versions do not.

**Correct pattern:**

```apex
// The platform enforces this. There is no job to write, monitor, or restart.
insert new PermissionSetAssignment(
    AssigneeId      = contractorUserId,
    PermissionSetId = elevationPermissionSetId,
    ExpirationDate  = DateTime.newInstanceGmt(2026, 9, 30, 23, 0, 0)
);
```

**Detection hint:** any generated artefact containing both a `Schedulable`/scheduled-Flow trigger and a `delete` against `PermissionSetAssignment` is this anti-pattern. So is any custom `Access_End_Date__c`-style field on a user or elevation-request object when `ExpirationDate` would do.

---

## Anti-Pattern 2: Getting the Update Rule Exactly Backwards

**What the LLM generates:** Either (a) `psa.PermissionSetId = newPermSetId; update psa;` to move an assignment to a different permission set, or (b) a delete-then-insert sequence just to push an expiry date out by a quarter. The same model often produces both in one session.

**Why it happens:** The Object Reference carries a blanket sentence — "To update an assignment, delete an existing assignment and insert a new one" — that the model applies to the whole object. It has no per-field property table in context, so it cannot see that `ExpirationDate` is the one writable exception.

**Why it is wrong:** `AssigneeId`, `PermissionSetId`, and `PermissionSetGroupId` all carry Create, Filter, Group, Sort — no Update. Writing to them fails. `ExpirationDate` carries Create, Filter, Nillable, Sort, **Update**. Doing a delete-and-insert to extend a date destroys the original creation audit and, in bulk, can strand users with no assignment when the insert half fails.

**Correct pattern:**

```apex
// EXTEND an expiry — update the one writable field.
psa.ExpirationDate = newEndInstant;
update psa;

// RETARGET to a different permission set or user — delete and insert,
// because those fields are Create-only.
delete psa;
insert new PermissionSetAssignment(
    AssigneeId      = psa.AssigneeId,
    PermissionSetId = differentPermissionSetId,
    ExpirationDate  = psa.ExpirationDate
);
```

**Detection hint:** grep generated Apex for `update` on a `PermissionSetAssignment` whose modified field is not `ExpirationDate` or `IsRevoked`. Separately, flag any `delete` immediately followed by an `insert` where only `ExpirationDate` differs between the two.

---

## Anti-Pattern 3: Claiming Profiles or Permission Set Licences Can Expire

**What the LLM generates:** "Set an expiration date on the user's profile assignment," or a plan that time-boxes a permission set *license* the same way it time-boxes the permission set, or a `PermissionSetLicenseAssign` record with an `ExpirationDate` field.

**Why it happens:** The model generalises from "permission set assignments can expire" to the whole permission model, because all of these read as "assignment" objects with similar names.

**Why it is wrong:** the field exists on exactly one object in this family.

**Correct pattern:**

```
Can carry ExpirationDate:
  PermissionSetAssignment  → PermissionSetId      (a permission set)
  PermissionSetAssignment  → PermissionSetGroupId (a permission set group)

Cannot:
  PermissionSetLicenseAssign  no ExpirationDate field; supported calls are
                              create/delete/describeSObjects/query/retrieve
                              — update() is not among them
  Profile                     a lookup on User; there is no assignment object
  MutingPermissionSet         a component of a permission set group, never
                              assigned to a user
  GroupMember                 two fields, GroupId and UserOrGroupId, no update()
  Package license             user access policies can Grant/Revoke it, with no
                              date attached
```

**Detection hint:** any generated SOQL selecting or filtering `ExpirationDate` from an object other than `PermissionSetAssignment` is wrong. Any prose promising a time-boxed licence is wrong.

---

## Anti-Pattern 4: Audit Queries That Assume the Assignment Disappears

**What the LLM generates:**

```soql
-- "Who currently has the elevated permission set?"
SELECT Assignee.Name FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'PS_Temp_ManageUsers'
```

with no state predicate, presented as the answer to a compliance question.

**Why it happens:** Before expiry existed, the presence of the row *was* the answer, and the overwhelming majority of `PermissionSetAssignment` examples in training data predate `ExpirationDate`.

**Why it is wrong:** liveness is carried by `IsActive`, a platform-owned, read-only field, not by the row's existence. Separately, in an org with user access policies enabled, a policy revocation sets `IsRevoked = true` and leaves the record in place — the Object Reference's own retrieval example for that population uses `ALL ROWS`. One query covers neither terminal state.

**Correct pattern:**

```soql
-- Live grants
SELECT Assignee.Name, ExpirationDate FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'PS_Temp_ManageUsers' AND IsActive = true

-- Lapsed grants (ALL ROWS is correct whether or not lapsed rows are hidden)
SELECT Assignee.Name, ExpirationDate FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'PS_Temp_ManageUsers' AND IsActive = false ALL ROWS

-- Policy-revoked grants — a different terminal state entirely.
-- Select the change ID: the Object Reference prints the relationship name
-- for LastDeletedByChangeId as LastCreatedByChange, so an inline
-- LastDeletedByChange.Source traversal is not a documented shape.
SELECT Assignee.Name, ExpirationDate, LastDeletedByChangeId
FROM PermissionSetAssignment WHERE IsRevoked = true ALL ROWS
```

**Detection hint:** flag any `PermissionSetAssignment` query offered as a compliance or access-review answer that lacks both an `IsActive` predicate and an `IsRevoked` companion query. Flag `LastDeletedByChange.Source` too — it is the relationship name a model expects rather than the one the Object Reference prints.

---

## Anti-Pattern 5: Asserting a Specific Expiry Clock Time from Memory

**What the LLM generates:** Confident sentences of the form "the assignment expires at HH:MM in the org's default time zone" or "expiration always occurs at midnight," stated flatly and without a source, often inside a runbook an auditor will read.

**Why it happens:** The detail is memorable, it appears in third-party blog posts with mutually inconsistent values, and the model has no signal that the authoritative page is one it cannot reach.

**Why it is wrong:** the exact clock time and time-zone semantics of the Setup assignment screen are documented only in Salesforce Help, which does not render to any fetcher. Third-party sources on this specific number disagree with each other. A wrong cutoff time in a security runbook is a promise to an auditor that the org cannot keep.

**Correct pattern:**

```
Say this:
  ExpirationDate is a dateTime. Through the API, write an explicit instant so
  the cutoff is unambiguous. Through Setup, confirm what clock time and time
  zone the org's assignment screen applies before quoting a cutoff to anyone.

Do NOT say:
  "It expires at <time> in <time zone>."  — unless you have the current
  Salesforce Help page in front of you and are quoting it.
```

**Detection hint:** grep generated guidance for a clock time next to the words "expire" or "expiration". Any such number without an adjacent, fetched citation should be deleted, not softened.

---

## Anti-Pattern 6: Time-Boxing the Job-Function Permission Set Group

**What the LLM generates:** "Assign `PSG_SupportAgent_Prod` with an `ExpirationDate` of 30 September" — attaching the date to whatever permission set group the user already has, because that is the group the conversation mentioned.

**Why it happens:** The model optimises for the fewest new objects. Reusing an existing group looks like good hygiene and avoids proposing a new permission set the user did not ask for.

**Why it is wrong:** the group carries the user's permanent access as well as the temporary capability. When the date passes, the user loses their day job. The Security Guide's rule cuts the other way too — since permissions aggregate, attaching a date to a broad group is simultaneously too destructive (it removes everything) and too weak (the elevated permission may also sit on the profile).

**Correct pattern:**

```
Unit of expiry = the smallest grant containing ONLY the temporary capability.

  One capability, one person, fixed window
      → new single-purpose permission set + ExpirationDate

  An entire role is temporary (project, migration cutover, audit window)
      → permission set group + ExpirationDate is correct

  Never: an expiry on a group that also carries permanent day-to-day access.
```

**Detection hint:** if the permission set or group named in the expiry is the same one the user was already assigned for their normal work, flag it and propose a narrow elevation set instead.

---

## Anti-Pattern 7: Inventing a Time Limit on a User Access Policy

**What the LLM generates:** A `UserAccessPolicy` metadata file with an invented `<expirationDate>`, `<duration>`, or `<expiresAfterDays>` element inside `<userAccessPolicyActions>`, or prose claiming a policy can "grant this permission set for 90 days."

**Why it happens:** Automated provisioning and time-bounded access are adjacent problems, so the model assumes the automation engine owns the clock.

**Why it is wrong:** `UserAccessPolicyAction` has exactly three fields — `action` (`Grant` or `Revoke`), `target`, and `type` (`Group`, `PackageLicense`, `PermissionSet`, `PermissionSetGroup`, `PermissionSetLicense`, `Queue`). There is no date anywhere in the policy metadata. Policies express "access follows the attribute"; only `ExpirationDate` expresses "access lasts until this instant." An invented element fails deployment, and the accompanying prose sends the architect down a design that cannot be built.

**Correct pattern:**

```xml
<!-- force-app/main/default/useraccesspolicies/Sales_Rep_Migration.useraccesspolicy-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<UserAccessPolicy xmlns="http://soap.sforce.com/2006/04/metadata">
    <booleanFilter>1</booleanFilter>
    <masterLabel>Sales Rep Migration</masterLabel>
    <status>Design</status>
    <triggerType>CreateAndUpdate</triggerType>
    <userAccessPolicyActions>
        <action>Grant</action>
        <target>SalesRepPSG</target>
        <type>PermissionSetGroup</type>
    </userAccessPolicyActions>
    <userAccessPolicyFilters>
        <operation>equals</operation>
        <sortOrder>1</sortOrder>
        <target>SalesRepCustomProfile</target>
        <type>Profile</type>
    </userAccessPolicyFilters>
</UserAccessPolicy>
```

Note also that a policy deployed with `<status>Active</status>` comes back as `Design` — an admin activates it in Setup. Deployment does not turn a policy on.

**Detection hint:** grep generated `.useraccesspolicy-meta.xml` for any element inside `<userAccessPolicyActions>` other than `action`, `target`, and `type`.

---

## Anti-Pattern 8: Handing the Admin a Click Trail That Does Not Exist in Their Org

**What the LLM generates:** Confident Setup instructions — "on the assignment screen, set the expiration date" — with no check that the control is present, and often routed through the user record rather than the permission set.

**Why it happens:** The model has no view of the target org's settings and defaults to describing the feature as universally visible.

**Why it is wrong:** two separate gates. `UserManagementSettings.psaExpirationUIEnabled` is documented as defaulting to `false`, so in an org that never turned it on there is no expiration control to click. And the Security Guide's expiration step sits in the permission-set-side *Manage Assignments → Add Assignments* flow, not in the user-record-side *Edit Assignments* procedure. An admin following a confident, wrong click trail concludes the feature does not exist in their edition.

**Correct pattern:**

```
1. Check the gate first, in metadata rather than by clicking:
     sf project retrieve start --metadata "Settings:UserManagement"
   Look for <psaExpirationUIEnabled>true</psaExpirationUIEnabled>.
   Absent or false → the Setup screens show no expiration control.

2. Then give the path that actually carries the step:
     Setup → Permission Sets → <the set> → Manage Assignments
           → Add Assignments → select users → Next → set expiration → Assign
   Requires: Assign Permission Sets AND View Setup and Configuration.

3. For guest, Self-Service, integration, and system users, skip the UI —
   they are not available on the Manage Assignments page. Use the
   PermissionSetAssignment API object.
```

**Detection hint:** any Setup-path answer about expiration that does not first establish `psaExpirationUIEnabled`, or that routes through the user record's Edit Assignments page, should be rewritten.
