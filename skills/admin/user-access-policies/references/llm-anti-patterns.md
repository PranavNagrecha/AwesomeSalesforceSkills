# LLM Anti-Patterns — User Access Policies

Common mistakes AI coding assistants make when generating or advising on User Access Policies.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Apex Triggers Instead of UAP for Standard Provisioning

**What the LLM generates:** A trigger on the User object's `after insert` and `after update` events that queries permission sets and calls `insert new PermissionSetAssignment(...)` to assign permissions based on Profile or Department.

**Why it happens:** LLMs have extensive training data on Apex triggers for permission assignment, which was the standard approach before UAP GA. The Apex pattern is well-represented; UAP is newer and less represented in training data.

**Correct pattern:**

```text
Use a User Access Policy Grant policy with filter criteria matching the
user attribute (Profile, Department, Role). No Apex code is required.
UAP is the preferred no-code alternative for attribute-based provisioning
as of Spring '25 (release 242).
```

**Detection hint:** Look for `PermissionSetAssignment` in Apex trigger context on the User object — this is the signal that the LLM defaulted to the Apex approach when UAP should be considered first.

---

## Anti-Pattern 2: Assuming UAP Backfills Existing Users on Activation

**What the LLM generates:** Instructions stating "once you activate the policy, all users matching the criteria will automatically receive the permission set" without noting the forward-only evaluation behavior.

**Why it happens:** LLMs generalize from other automation tools (Process Builder, Flow, assignment rules) that do offer bulk evaluation options. They apply this expectation to UAP incorrectly.

**Correct pattern:**

```text
UAP only evaluates on future user create or qualifying field update events.
Existing users who already match the filter are NOT retroactively updated
when a policy is activated. A separate bulk data operation is required
to bring existing users into compliance.
```

**Detection hint:** Look for phrases like "all existing users will receive" or "retroactively assigned" following UAP activation steps — these indicate the backfill assumption error.

---

## Anti-Pattern 3: Claiming UAP Supports OR Logic in Filter Criteria

**What the LLM generates:** A policy configuration showing `Profile = Sales OR Profile = Marketing` as a single filter condition, or instructions to use OR operators in UAP filter criteria.

**Why it happens:** LLMs familiar with SOQL WHERE clauses, Flow conditions, and other Salesforce tools that support OR logic assume UAP shares the same filter expressiveness.

**Correct pattern:**

```text
UAP filter criteria support AND logic only. To target users matching
Profile = Sales OR Profile = Marketing, create two separate Grant policies:
  - Policy 1: filter Profile = Sales
  - Policy 2: filter Profile = Marketing
Each policy is independent and evaluated separately.
```

**Detection hint:** Look for "OR" in any UAP filter criteria description — UAP does not support OR logic; separate policies must be created.

---

## Anti-Pattern 4: Ignoring Evaluation Order When Designing Overlapping Policies

**What the LLM generates:** Grant and Revoke policy configurations targeting the same permission set and the same user filter criteria without noting that the revoke will always override the grant.

**Why it happens:** LLMs describe each policy in isolation without modeling the evaluation-order interaction. They often present grant and revoke as symmetrical operations that can coexist for the same user segment.

**Correct pattern:**

```text
Grant policies always evaluate before Revoke policies. If the same user
matches both a Grant and a Revoke policy for the same permission set,
the revoke takes effect. Grant and Revoke filter criteria must be
mutually exclusive for a given permission set to avoid this conflict.
```

**Detection hint:** Check if any permission set appears in both a Grant and a Revoke policy with overlapping filter criteria — this is the conflict pattern.

---

## Anti-Pattern 5: Omitting the Need to Deactivate Conflicting Apex Triggers

**What the LLM generates:** UAP setup instructions that add UAP policies without mentioning that existing Apex triggers handling the same permission assignments must be deactivated first.

**Why it happens:** LLMs treat UAP as a purely additive configuration step and do not model the interaction between declarative and programmatic automation running simultaneously on the same object.

**Correct pattern:**

```text
Before activating UAP policies, identify all active Apex triggers on the
User object that assign or revoke the same permission sets. Deactivate
or delete those triggers. Running both UAP and an Apex trigger for the
same permission sets simultaneously can cause MIXED_DML errors,
duplicate assignments, or conflicting final permission states.
```

**Detection hint:** Any UAP setup plan that does not include a step for auditing and deactivating existing Apex triggers is likely missing this critical prerequisite.
