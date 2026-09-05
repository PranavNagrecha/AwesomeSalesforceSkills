# LLM Anti-Patterns — User Access Policies

Common mistakes AI coding assistants make when generating or advising on User Access Policies.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Apex Triggers Instead of UAP for Standard Provisioning

**What the LLM generates:** A trigger on the User object's `after insert` and `after update` events that queries permission sets and calls `insert new PermissionSetAssignment(...)` to assign permissions based on Profile or Department.

**Why it happens:** LLMs have extensive training data on Apex triggers for permission assignment, which was the standard approach before UAP existed. The Apex pattern is well-represented; UAP is newer and less represented in training data.

**Correct pattern:**

```xml
<UserAccessPolicy xmlns="http://soap.sforce.com/2006/04/metadata"><!-- excerpt: fragment of a policy definition -->
<!-- A UserAccessPolicy replaces the trigger entirely. No Apex, no test class,
     no bulkification, and it is deployable metadata like any other component. -->
<userAccessPolicyFilters>
    <operation>equals</operation>
    <sortOrder>1</sortOrder>
    <target>SalesRepCustomProfile</target>
    <type>Profile</type>
</userAccessPolicyFilters>
<userAccessPolicyActions>
    <action>Grant</action>
    <target>SalesRepPSG</target>
    <type>PermissionSetGroup</type>
</userAccessPolicyActions>
</UserAccessPolicy>
```

**Detection hint:** Look for `PermissionSetAssignment` DML in Apex trigger context on the User object — this is the signal that the LLM defaulted to the Apex approach when UAP should have been considered first. Reserve Apex for logic UAP's filter schema cannot express: cross-object traversal, computed values, conditional branching.

---

## Anti-Pattern 2: Assuming UAP Backfills Existing Users on Activation

**What the LLM generates:** Instructions stating "once you activate the policy, all users matching the criteria will automatically receive the permission set" without noting the event-driven evaluation behavior.

**Why it happens:** LLMs generalize from other automation tools (Flow, assignment rules) that do offer bulk evaluation options. They apply this expectation to UAP incorrectly.

**Correct pattern:**

```text
triggerType is Create, Update, or CreateAndUpdate — every value describes an
event on a user record. A user who already matches the criteria and is not
subsequently created or updated is not evaluated. Plan a separate one-time
operation for the existing population; do not size a security remediation
around policy activation.
```

**Detection hint:** Look for phrases like "all existing users will receive" or "retroactively assigned" following UAP activation steps. See `references/gotchas.md` Gotcha 10 for the grounding boundary on this claim.

---

## Anti-Pattern 3: Claiming UAP Filters Are AND-Only and Splitting the Policy to Fake OR

**What the LLM generates:** A confident statement that "UAP filter criteria support AND logic only," followed by advice to create two policies — one filtering `Profile = Sales`, one filtering `Profile = Marketing` — to cover a population that either profile qualifies for.

**Why it happens:** Several older declarative Salesforce filter surfaces are AND-only, and the training data conflates them. The advice sounds cautious, which makes it convincing, and the resulting policies deploy cleanly — so nothing fails at the point the mistake is made.

**Why it is actively harmful:** UAP supports OR two different ways, and the workaround it recommends is worse than wrong. Two policies matching an overlapping population compete rather than combine: only the active policy with the lowest `order` value is applied, so the second policy's actions never run for anyone the first also matched.

**Correct pattern:**

```xml
<UserAccessPolicy xmlns="http://soap.sforce.com/2006/04/metadata"><!-- excerpt: fragment of a policy definition -->
<!-- Two attributes, either qualifies: booleanFilter supports OR directly. -->
<booleanFilter>1 OR 2</booleanFilter>
<userAccessPolicyFilters>
    <operation>equals</operation>
    <sortOrder>1</sortOrder>
    <target>SalesRepCustomProfile</target>
    <type>Profile</type>
</userAccessPolicyFilters>
<userAccessPolicyFilters>
    <operation>equals</operation>
    <sortOrder>2</sortOrder>
    <target>MarketingCustomProfile</target>
    <type>Profile</type>
</userAccessPolicyFilters>
</UserAccessPolicy>
```

```xml
<UserAccessPolicy xmlns="http://soap.sforce.com/2006/04/metadata"><!-- excerpt: fragment of a policy definition -->
<!-- Several values of the SAME attribute: one row, operation in,
     comma-separated developer names in target (API v58.0+). -->
<booleanFilter>1</booleanFilter>
<userAccessPolicyFilters>
    <operation>in</operation>
    <sortOrder>1</sortOrder>
    <target>SalesOps,InsideSalesRep</target>
    <type>UserRole</type>
</userAccessPolicyFilters>
</UserAccessPolicy>
```

**Detection hint:** Flag any output containing "UAP does not support OR", "AND logic only", or a recommendation to duplicate a policy per value of one field. Also flag a policy with no `booleanFilter` element — it is required, even when its value is just `1`.

---

## Anti-Pattern 4: Modelling Conflict Resolution as "Grant Runs, Then Revoke Runs"

**What the LLM generates:** An explanation that the platform evaluates all grant policies first and all revoke policies second, so "the revoke always wins" when both match the same user — often paired with treating Grant and Revoke as two policy *types* or record types.

**Why it happens:** Grant-then-revoke is how a lot of entitlement systems work, and the symmetry is a natural-sounding abstraction. The LLM describes each policy in isolation and invents an ordering rule to reconcile them.

**Why it is actively harmful:** It gets both the unit and the mechanism wrong. Grant and Revoke are `action` values on `UserAccessPolicyAction`, a child of a single policy — one policy can contain both. And conflict resolution between *policies* is by the `order` field: only the active policy with the lowest `order` value is applied. Advice built on "revoke wins" tells the reader to make grant and revoke criteria mutually exclusive, when the real requirement is to assign distinct `order` values and account for the fact that a losing policy's grants never run at all.

**Correct pattern:**

```text
Within one policy: userAccessPolicyActions is a list of {action, target, type}
triples. Grant and Revoke coexist and both run.

Across policies: order is an int 0-10,000, required when status is Active.
Only the active policy with the lowest order is applied. Anything a suppressed
policy was granting must be repeated in the policy that outranks it.
```

**Detection hint:** Flag "grant policies run first", "revoke wins", "Grant policy type", "Revoke policy type", or any advice to make grant and revoke criteria mutually exclusive. Flag any policy set where two active policies share an `order` value or omit it.

---

## Anti-Pattern 5: Calling the UAP-versus-Trigger Overlap a MIXED_DML Problem

**What the LLM generates:** A warning that leaving an Apex trigger active alongside a UAP policy "can cause MIXED_DML exceptions", offered as the reason to deactivate the trigger.

**Why it happens:** `MIXED_DML_OPERATION` is the best-known exception associated with `User` and `PermissionSetAssignment`, so it gets attached to any scenario involving both. The recommendation that follows it happens to be right, which hides the fact that the reasoning is not.

**Why it is actively harmful:** It describes the wrong failure and therefore the wrong fix. `MIXED_DML_OPERATION` is raised when a *single transaction* mixes DML on a setup sObject (`User`, `PermissionSet`, `PermissionSetAssignment`, `Group`, `GroupMember`, `QueueSObject`, and others) with DML on a non-setup sObject — the Apex Developer Guide's stated reason is that these objects affect record access, so they must be committed in a separate transaction. A declarative policy and an Apex trigger run in separate transactions; that exception does not apply. A reader who accepts the framing goes looking for a `@future` wrapper and leaves both writers live.

**Correct pattern:**

```text
Real risk of running both: two independent writers of the same
PermissionSetAssignment rows, with no platform-defined ordering between
them. The final state belongs to whichever wrote last. Fix: cut over —
deactivate the trigger in the same release that activates the policy.

Real MIXED_DML risk, separately: an Apex trigger or test that inserts a User
and a PermissionSetAssignment alongside ordinary record DML in one
transaction. Fix: move the setup-object DML into a @future method.
```

**Detection hint:** Flag "MIXED_DML" appearing anywhere near a comparison of UAP and triggers as *concurrent automations*. Accept it only where the sentence is about a single Apex transaction's own DML.

---

## Anti-Pattern 6: Generating Code or Loads That Write to `UserAccessPolicy`

**What the LLM generates:** An Apex script, a Data Loader plan, or a REST call that inserts or updates `UserAccessPolicy` records — for example, an org-setup routine that "creates the policies" the way it creates permission sets. Related: SOQL against `PermissionSetAssignment.IsRevoked` or `LastCreatedByChangeId` in an org where user access policies were never enabled.

**Why it happens:** The object appears in the Object Reference with a normal field table, and LLMs default to assuming a queryable sObject is also writable. The UAP-gated fields likewise look like ordinary fields in the schema documentation.

**Correct pattern:**

```text
UserAccessPolicy supported calls: describeSObjects(), query(), retrieve().
No create, update, delete, or upsert. No REST resource, no Bulk API path,
no Apex class. Authoring is a .useraccesspolicy Metadata API deployment or
the Setup UI; SOQL is read-only verification.

IsRevoked, LastCreatedByChangeId, and LastDeletedByChangeId exist on
PermissionSetAssignment only when user access policies are enabled — code
referencing them will not compile in an org where the feature is off.
```

**Detection hint:** Flag any DML, `Database.insert`, upsert plan, or Bulk job whose target is `UserAccessPolicy` or `UserAccessChange`. Flag any query on `IsRevoked` / `LastCreatedByChange*` that is not preceded by a check that `userAccessPoliciesEnabled` is true in the target org.
