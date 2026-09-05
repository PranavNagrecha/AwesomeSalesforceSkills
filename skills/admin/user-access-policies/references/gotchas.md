# Gotchas — User Access Policies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Only the Lowest-`order` Active Policy Runs — Matching Policies Do Not Stack

**What happens:** A user who satisfies the criteria of three active policies gets the actions of exactly one of them. The Metadata API guide's `order` field states it plainly: the value "indicates the order for which active policy is applied when a user meets the criteria for multiple policies... Only the active policy with the lowest `order` value is applied." The Object Reference repeats it on the sObject's `Order` field. The other two policies' grants and revokes do not execute, do not queue, and leave no trace.

**When it occurs:** Whenever an org grows past one policy. It is most damaging when a broad "everybody gets the baseline seat" policy is written first and a narrow regional or role-specific policy is added later with a lower `order` — the newer, narrower policy silently suppresses the baseline grant for exactly the people it was meant to *add* to.

**How to avoid:** Treat the policy set as a ranked list, not a set of independent rules. Keep a register of every active policy and its `order` value alongside the criteria it matches, and before adding a policy, ask which existing policy it will outrank and which grants that policy was contributing. Anything a suppressed policy was granting has to be repeated in the winning policy. `scripts/check_user_access_policies.py` reports duplicate `order` values and flags policies whose criteria overlap.

---

## Gotcha 2: A Policy Deployed with `status` `Active` Arrives as `Design`

**What happens:** The deployment succeeds, the policy exists in the target org, and it is not running. The `status` field's documentation states: "If you deploy a policy with a status of Active, the status is changed to Design. A Salesforce admin can then set the status to Active by automating the policy in Setup." There is no error, no warning in the deploy result, and no difference in the component status.

**When it occurs:** Every promotion through a CI/CD pipeline, and every change set. Teams that verify a release by checking the deployment succeeded — rather than by creating a test user — ship a dead policy and find out weeks later when someone notices nobody was provisioned.

**How to avoid:** Deploy the file with `<status>Design</status>` so the artifact matches reality, and put the Setup activation on the release runbook with a named owner. Verify with `SELECT DeveloperName, Status FROM UserAccessPolicy` after activation, not after deployment. The `Order` field is required only when the status is `Active`, so a policy sitting in `Design` also has no conflict-resolution semantics yet.

---

## Gotcha 3: `booleanFilter` Is Required, and It Supports OR

**What happens:** `booleanFilter` is a required field on every policy, including one with a single filter row (where its value is just `1`). Omitting it fails the deployment. More consequentially, practitioners and AI assistants routinely believe UAP filters are AND-only and fan a single population out into several near-identical policies to fake OR — which then lose to each other on `order` (Gotcha 1). The guide's wording is explicit: "if you have two user access policy filters with the `sortOrder` equal to 1 and 2, respectively, the `booleanFilter` can be `1 AND 2` or `1 OR 2`."

**When it occurs:** On the first policy an author writes, and on every policy migrated from an AND-only mental model. It also occurs when filter rows are renumbered or deleted without updating `booleanFilter`, leaving a number in the expression with no matching `sortOrder`.

**How to avoid:** Write the `sortOrder` values first, then the `booleanFilter` expression over them. Express alternatives with `OR` inside one policy instead of splitting into competing policies. The checker script cross-references every integer in `booleanFilter` against the declared `sortOrder` values and reports both dangling references and rows the expression never mentions.

---

## Gotcha 4: `operation` `in` Is a Second, Independent Way to Match Several Values

**What happens:** A single filter row can match multiple profiles or roles without `booleanFilter` involvement at all. The guide states: "Select `in` if you want to reference multiple profiles or roles in the same user criteria filter via the target field," and its own sample puts `SalesOps,InsideSalesRep` in one `target` element. This is available in API version 58.0 and later; `equalsIgnoreCase` and `includes` arrived in 59.0.

**When it occurs:** Any time several sibling roles or profiles share a seat. Authors who only know `equals` write one row per value plus a long `1 OR 2 OR 3` expression, which works but is harder to maintain, or — worse — one policy per value, which reintroduces the `order` problem.

**How to avoid:** Use `in` with a comma-separated `target` for several values of the *same* attribute; use `booleanFilter` `OR` for several *different* attributes. Check the org's API version before using `in` — a policy deployed at an API version below 58.0 has no such operator.

---

## Gotcha 5: `order` Is Bounded at 0–10,000 and Must Be Chosen, Not Defaulted

**What happens:** The field is an `int` constrained to "an integer from 0 to 10,000" and is available in API version 61.0 and later. Two active policies sharing an `order` value have no documented tiebreak in the Metadata API guide or the Object Reference, so which one wins for an overlapping user is not something the metadata tells you. Sparse numbering is not free either: there is no room to insert between 10,000 and anything above it.

**When it occurs:** In orgs that number policies 1, 2, 3 as they are created and then need to slot a more specific policy above an existing one, or in orgs that leap to large round numbers and hit the ceiling.

**How to avoid:** Number in gaps — 100, 200, 300 — so a policy can be inserted later without renumbering, and stay well under the ceiling. Make every active policy's `order` unique. The checker enforces both the range and uniqueness across policies in the manifest.

---

## Gotcha 6: `UserAccessPolicy` Cannot Be Created or Updated Through the API

**What happens:** The `UserAccessPolicy` standard object supports only `describeSObjects()`, `query()`, and `retrieve()`. There is no `create()`, `update()`, `delete()`, or `upsert()`; no REST resource, no Bulk API path, no Apex class. A script that tries to provision policies the way it would provision `PermissionSetAssignment` rows has nowhere to write. Authoring is Metadata API deployment of a `.useraccesspolicy` file, or the Setup UI.

**When it occurs:** In org-setup automation and in migration tooling that treats every configuration object as loadable. Also in AI-generated "seed the org" scripts, which reach for `Database.insert` on anything with an sObject name.

**How to avoid:** Keep policies in source control as `.useraccesspolicy` files and deploy them; use SOQL only to read what is deployed. Reading the object requires **Manage User Access Policies**, the same permission the guide names as required to create or modify a policy.

---

## Gotcha 7: `UserAccessChange` — Not the Setup Audit Trail — Is the Provenance Record

**What happens:** UAP provisioning writes a queryable `UserAccessChange` record, and `PermissionSetAssignment` gains three fields when the feature is enabled: `IsRevoked`, `LastCreatedByChangeId`, and `LastDeletedByChangeId`, the last two lookups to `UserAccessChange`. The change record's `Source` field names where the change came from — the Object Reference's example value is `UserAccessPolicyId`. The critical consequence is the converse: **those three fields do not exist in an org where user access policies are not enabled**, so a query or Apex class referencing them fails to compile there.

**When it occurs:** During audits ("prove no human granted this"), and during deployments of Apex or reports that reference `IsRevoked` into a sandbox where the feature was never switched on.

**How to avoid:** Query `PermissionSetAssignment.LastCreatedByChange.Source` to distinguish policy-driven grants from manual ones, and use `IsRevoked` to tell a UAP revocation from a deleted row. Reading `UserAccessChange` needs **View Setup and Configuration**. Gate any code or report that touches these fields on the feature being enabled in the target org, and deploy the `userAccessPoliciesEnabled` setting first.

---

## Gotcha 8: MIXED_DML Is About One Transaction, Not About Two Competing Automations

**What happens:** `MIXED_DML_OPERATION` is raised when a single transaction performs DML on a "setup" sObject and a non-setup sObject together. The Apex Developer Guide's reason is access-level correctness: "some sObjects affect the user's access to records in the org. You must insert or update these types of sObjects in a different transaction to prevent operations from happening with incorrect access-level permissions." The listed setup objects include `User`, `PermissionSet`, `PermissionSetAssignment`, `Group`, `GroupMember`, `QueueSObject`, `ObjectPermissions`, and `FieldPermissions`. The rule for `User` is conditional rather than absolute — inserting a `User` alongside other sObjects is allowed at API 15.0+ when `UserRoleId` is null, and updating one is allowed when none of `UserRoleId`, `IsActive`, `ForecastEnabled`, `IsPortalEnabled`, `Username`, or `ProfileId` is being changed.

**When it occurs:** In an Apex trigger or test that creates a user and assigns a permission set alongside ordinary record DML. It is **not** what happens when a declarative policy and an Apex trigger both act on the same user — those are separate transactions, and the failure mode there is a contested final state, not this exception.

**How to avoid:** In Apex, move setup-object DML into a `@future` method — the guide's own sample comment is "If you assign permission sets, do it in a future method to avoid mixed DML." When reasoning about UAP-versus-trigger overlap, name the real risk: two independent writers of the same assignment rows with no defined ordering. Deactivate the trigger as a cutover rather than running both.

---

## Gotcha 9: A Public-Group or Queue Action Does Not Write a `QueueSobject` Row

**What happens:** `Group` and `Queue` are both `UserAccessPolicyActionTargetType` values, but they land in different places in the object model. A queue is a `Group` whose `Type` is `Queue`, and membership of a public group or a queue is a `GroupMember` row against that `Group`. `QueueSobject` is a different object entirely — it maps which sObject types a queue can hold, not who is in it. The `GroupMember` documentation names user access policies in Setup as one of the supported ways to adjust public-group membership.

**When it occurs:** When someone verifies a `type` `Queue` action by querying `QueueSobject` and concludes nothing happened, or when a cleanup script deletes `QueueSobject` rows expecting to remove people from a queue.

**How to avoid:** Verify group and queue actions with `SELECT GroupId, UserOrGroupId FROM GroupMember WHERE UserOrGroupId = '<user id>'`. Reserve `QueueSobject` for the queue's supported object types. Note also that `Group`, `GroupMember`, and `QueueSObject` are all setup objects for mixed-DML purposes (Gotcha 8).

---

## Gotcha 10: Activation Does Not Reach Back Over Existing Users

**What happens:** Activating a policy does not sweep the existing user base. Evaluation is tied to `triggerType` — `Create`, `Update`, or `CreateAndUpdate` — all of which describe an event on a user record, so a user who already matches the criteria and is not subsequently touched is not evaluated. An admin who activates a grant policy and then looks for a wave of new assignments finds none.

> **UNVERIFIED (2026-09-05)** — grounded: the `triggerType` enum and its per-value descriptions, all of which are event-based. Not grounded: neither api_meta.txt nor object_reference.txt states in words that activation performs no retroactive evaluation, and neither documents what the `Migrate` status value does — it may cover a bulk-apply path. Confirm the backfill behaviour and `Migrate` against Salesforce Help before relying on this gotcha.

**When it occurs:** On first adoption in an org with a live user base, and after any policy change that widens the criteria — the newly-qualifying users are not re-evaluated until something touches their records.

**How to avoid:** Plan a separate one-time operation for the existing population: a bulk update that touches a field the policy filters on, or a direct `PermissionSetAssignment` load. Do not size a security remediation around policy activation. Note the related trap: a filter built on a field that no provisioning process actually updates gives you a policy that is technically correct and never fires — prefer attributes the HR or identity integration genuinely writes.

> **UNVERIFIED (2026-09-05)** — the stronger form of the last sentence, that re-evaluation fires *only* when a field named in a filter is updated (rather than on any user update while `triggerType` is `Update` or `CreateAndUpdate`), is not stated in api_meta.txt or object_reference.txt. The advice above is deliberately phrased to hold either way; do not tighten it without a Salesforce Help citation.

---

## Gotcha 11: A Permission Set Licence Grant Is an Independent Action

**What happens:** Each `userAccessPolicyActions` element is a self-contained `{action, target, type}` triple. Granting a `PermissionSetLicense` and granting the `PermissionSet` that consumes it are two separate actions, and the Metadata API guide documents no interaction rule between action rows — nothing in the schema causes one to imply the other.

> **UNVERIFIED (2026-09-05)** — the stronger claim this skill previously made, that assigning a permission set licence via UAP does not automatically assign the permission set consuming it, is a runtime licence behaviour not documented in the `UserAccessPolicyAction` section of api_meta.txt. Grounded here is only the structural point above: actions are independent `{action, target, type}` triples with no documented coupling between rows. Verify the runtime behaviour in a sandbox before relying on it.

**When it occurs:** On licence-gated features where the seat needs both a licence and a permission set group. It compounds with Gotcha 1: if the licence grant sits in a policy that a narrower policy outranks, the licence is never granted for the users the narrower policy claims.

**How to avoid:** Put the licence action and the permission set or permission set group action in the same policy, and repeat that pair in any policy that could outrank it for the same population. Verify a real test user has both before declaring the seat provisioned.
