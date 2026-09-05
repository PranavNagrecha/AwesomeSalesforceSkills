---
name: user-access-policies
description: "Configuring User Access Policies (UAP) to automatically assign or revoke permission sets and permission set groups based on user attributes. Use when automating permission provisioning on user create/update without Apex triggers. Covers policy configuration, filter criteria, evaluation order, and PSL assignment. Also covers booleanFilter OR logic, the `in` operator for multi-value filters, the `order` tiebreak between competing policies, actions incl. permission set / permission set group / permission set licence / package licence / queue / public group grant and revoke, the UserAccessChange audit object, and deploying the UserAccessPolicy metadata type. NOT for permission set design — use admin/permission-set-architecture. NOT for delegated user admin — use admin/delegated-administration."
category: admin
salesforce-version: "Spring '25+ (UserAccessPolicy metadata, API v57.0+)"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "automatically assign permission sets when user is created"
  - "revoke permission sets when user profile changes"
  - "automate permission provisioning without Apex triggers"
  - "login-based license assignment via user access policy"
  - "auto-provision permissions based on department or role"
  - "user access policy filter needs OR between two profiles"
  - "match multiple roles in one user access policy filter"
  - "two user access policies match the same user which one wins"
  - "deployed user access policy came back as Design not Active"
  - "grant and revoke in the same user access policy"
  - "find out which policy assigned a permission set to a user"
  - "add a user to a public group or queue automatically"
tags:
  - user-access-policies
  - permission-sets
  - provisioning
  - automation
  - admin
inputs:
  - "User field criteria used to identify target users (Profile, Role, UserType, Department, custom fields)"
  - "List of permission sets or permission set groups to grant or revoke"
  - "Target access mechanisms and their types (PermissionSet, PermissionSetGroup, PermissionSetLicense, PackageLicense, Group, Queue)"
  - "Whether the org has user access policies enabled (UserManagementSettings.userAccessPoliciesEnabled)"
outputs:
  - "Configured User Access Policy records with filter criteria and permission assignments"
  - "Deployable .useraccesspolicy metadata plus the package.xml entry"
  - "Review checklist verifying filter logic, order assignment, and PSL inclusion"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# User Access Policies

This skill activates when a practitioner needs to automate permission set, permission set group, permission set licence, package licence, public group, or queue assignment and revocation based on user attribute criteria, without writing Apex triggers. It guides policy configuration, filter setup, `order` resolution, and deployment of the `UserAccessPolicy` metadata type (available in API version 57.0 and later, Metadata API Developer Guide, "UserAccessPolicy" → Version).

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm user access policies are enabled in the org — `UserManagementSettings.userAccessPoliciesEnabled` (API v58.0+). Where the improved authoring UI is wanted, `enableEnhcUiUserAccessPolicies` (API v60.0+) is set to `true` automatically when the feature is enabled, and can be turned back off.
- Confirm the authoring user holds the **Manage User Access Policies** permission — the Metadata API guide states it is required to create or modify user access policies (`UserAccessPolicy` → Special Access Rules).
- Identify which user attributes will serve as filter criteria. A filter row is typed: `Profile`, `UserRole`, `Group`, `Queue`, `PermissionSet`, `PermissionSetGroup`, `PermissionSetLicense`, `PackageLicense`, or `User` (a raw user field, named in `columnName` with its `value`).
- Know which access mechanisms are being granted or revoked. Both are `action` values on the same child element, so one policy can grant and revoke in a single definition.
- Confirm the target permission sets, permission set groups, permission set licences, package licences, public groups, and queues already exist in the org — `target` is a developer name and is resolved at deploy time.
- Decide the policy's `order` (0–10,000) relative to every other active policy, because only one policy applies when several match the same user.
- Identify whether existing Apex-based permission assignment triggers exist — UAP does not replace triggers automatically; leaving both live means two independent writers of the same `PermissionSetAssignment` rows.

---

## Questions to Ask Before Configuring

Ask these before creating the policy; the answers decide the shape of the XML, and an LLM that skips them writes a policy that deploys cleanly and provisions the wrong people.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is this one population, or several that happen to get the same access?" | One population with alternatives is `booleanFilter` `1 OR 2` or one `in` filter; several distinct populations are separate policies that then compete on `order` | Either a single policy definition, or a policy list with an assigned order range |
| "If a user matches this policy *and* another one, which should win?" | Only the active policy with the lowest `order` is applied — matching is not additive | A concrete integer per policy and a documented tiebreak, instead of an implicit one |
| "Which access mechanisms, exactly, and of what type?" | `type` is a restricted enum; `PermissionSetLicense` and `PackageLicense` are separate from `PermissionSet`, and public group vs queue membership are different targets | The exact `target`/`type` pairs for each `userAccessPolicyActions` element |
| "Should this run on create, on update, or both?" | `triggerType` is `Create`, `Update`, or `CreateAndUpdate`; a create-only policy never re-evaluates a transferring employee | The `triggerType` value, and whether a second policy is needed for the other event |
| "Who is going to activate it after the deploy?" | A policy deployed with `status` `Active` is forced back to `Design`; activation is a Setup step by an admin | A named owner and a post-deploy activation step in the runbook |
| "How will we prove afterwards that the policy did it, not a person?" | `UserAccessChange` and the `LastCreatedByChangeId` / `LastDeletedByChangeId` fields on `PermissionSetAssignment` only exist when UAP is enabled | A verification query written before go-live, not an argument after one |
| "Does an Apex trigger already write these assignments?" | Two independent writers on the same rows produce a state that neither owns | A cutover decision — deactivate the trigger — rather than an additive rollout |

What a proper configuration adds over just clicking through Setup: the filter expresses the real population in one policy instead of a fan of near-duplicates, the `order` values are chosen rather than defaulted so the winner is predictable, activation is an explicit owned step after deployment, and every grant is provable from `UserAccessChange` at audit time.

---

## Core Concepts

### One Policy, Many Actions — Grant and Revoke Are Not Policy Types

Grant and revoke are `action` values on a `UserAccessPolicyAction` child element, not separate policy record types. A single `UserAccessPolicy` carries a list of `userAccessPolicyActions`, each an independent `{action, target, type}` triple:

| Element | Values | Note |
|---|---|---|
| `action` | `Grant`, `Revoke` | Required |
| `target` | developer name of the access mechanism | Required |
| `type` | `Group`, `PackageLicense`, `PermissionSet`, `PermissionSetGroup`, `PermissionSetLicense`, `Queue` | Required |

So one policy can grant a permission set group and revoke a stale public group in the same definition. There is no platform-level "grant pass then revoke pass": the actions on the one winning policy are what runs.

### Filter Criteria: Two Independent Ways to Express OR

`booleanFilter` is **required** and combines filter rows by their `sortOrder` — the guide's own wording is that "the `booleanFilter` can be `1 AND 2` or `1 OR 2`". OR logic is supported directly. A second, unrelated mechanism is the `in` operator on a single filter row: set `operation` to `in` and put comma-separated developer names in `target` to reference multiple profiles or roles in one row (API v58.0+).

| `operation` | Available from |
|---|---|
| `equals` | v57.0 |
| `notEquals` | v57.0 |
| `in` | v58.0 |
| `equalsIgnoreCase` | v59.0 |
| `includes` | v59.0 |

A filter row's `type` is one of `Group`, `PackageLicense`, `PermissionSet`, `PermissionSetGroup`, `PermissionSetLicense`, `Profile`, `Queue`, `User`, `UserRole`. When `type` is `User`, `target` is literally the string `User`, `columnName` names the user field, and `value` holds the value to compare — that is how a filter on `IsActive`, `Department`, or a custom user field is written.

### Conflict Resolution: Lowest `order` Wins, Single Winner

`order` is an integer from 0 to 10,000 (API v61.0+) and is required only when `status` is `Active`. When a user meets the criteria for multiple policies, **only the active policy with the lowest `order` value is applied**. The others do not run at all — their actions are not merged in, not appended, not applied afterwards. Design competing policies as a ranked list, most specific first.

### Status and the Deploy-Time Downgrade

`status` is required and takes `Active`, `Completed`, `Design`, `Failed`, `Migrate`, `Testing`, or `Updating`; the sObject default is `Design`. Deploying a policy with `status` `Active` does not activate it — the guide states the status is changed to `Design`, and an admin then sets it to `Active` by automating the policy in Setup. Every UAP deployment therefore has a manual post-step.

### Trigger Events

`triggerType` selects when the policy runs against a matching user: `Create` (on user creation), `Update` (on user update), or `CreateAndUpdate` (both). This is the only declarative control over when evaluation happens.

### Audit Surface

`UserAccessChange` is a real, queryable, read-only sObject (`describeSObjects()`, `getDeleted()`, `getUpdated()`, `query()`, `retrieve()`; no create/update/delete) whose `Source` field records where the change came from, "for example, `UserAccessPolicyId`". Reading it requires **View Setup and Configuration**. On `PermissionSetAssignment`, three fields exist *only* when user access policies are enabled: `IsRevoked`, `LastCreatedByChangeId`, and `LastDeletedByChangeId`, the latter two lookups to `UserAccessChange`. This is the provable trail, not the Setup Audit Trail.

---

## Common Patterns

### Pattern 1: One Policy, Two Profiles, One Grant

**When to use:** Two profiles (or roles) need the same permission set group, and you do not want two policies competing on `order`.

**How it works:**
1. Write one `userAccessPolicyFilters` row with `operation` `in`, `type` `Profile`, and `target` set to the comma-separated developer names.
2. Set `booleanFilter` to `1`.
3. Add one `Grant` action targeting the permission set group.
4. Deploy, then activate in Setup.

**Why not the alternative:** Two policies with identical actions would both match some users, and only the lower `order` would apply — so the second policy is dead weight that still has to be maintained and audited.

### Pattern 2: Grant and Revoke in the Same Policy on a Role Change

**When to use:** Moving into a role should add one access mechanism and remove another.

**How it works:**
1. Filter on the destination attribute (`type` `UserRole`, or `type` `User` with `columnName` `Department`).
2. Add a `Grant` action for the new permission set group and a `Revoke` action for the outgoing public group or permission set.
3. Set `triggerType` to `CreateAndUpdate` so the policy fires on the transfer, not only on hire.
4. Give it a low `order` so it beats the broader default-access policy.

**Why not the alternative:** Splitting grant and revoke across two policies makes them compete rather than cooperate — the higher-`order` one never runs for a user the lower one already matched.

### Pattern 3: Licence Plus Permission Set Group for a Gated Feature

**When to use:** A feature needs a permission set licence (or a managed-package licence) *and* the permission set group that consumes it.

**How it works:**
1. Filter on the population (`type` `User`, `columnName` `Department`, `value` the department name).
2. Add a `PermissionSetLicense` `Grant` action and a `PermissionSetGroup` `Grant` action to the same policy.
3. Add a `PackageLicense` `Grant` action too when the feature is delivered by a managed package.
4. Deploy and activate.

**Why not the alternative:** Splitting them across policies reintroduces the `order` problem — one policy wins, the other's licence grant never runs, and the seat looks half-provisioned.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Assign permissions on user create based on Profile | One policy, `type` `Profile` filter, `triggerType` `Create` | Declarative, deployable, auditable via `UserAccessChange` |
| Same access for two or more profiles/roles | One filter row with `operation` `in` and comma-separated `target` | Guide-documented multi-value matching; avoids competing policies |
| Two genuinely different criteria, either of which qualifies | One policy, two filter rows, `booleanFilter` `1 OR 2` | `booleanFilter` supports OR directly |
| Add and remove access in the same event | One policy with both `Grant` and `Revoke` actions | Actions are per-policy; both run when that policy is the winner |
| Several policies could match the same user | Assign distinct `order` values, most specific lowest | Only the lowest-`order` active policy applies; the rest do not run |
| Add a user to a public group or queue | `Grant` action with `type` `Group` or `Queue` | Both are `UserAccessPolicyActionTargetType` values |
| Policy needs cross-object lookups or branching logic | Apex, not UAP | Filters compare user attributes only; no traversal exists in the schema |
| Need the policy live immediately after deploy | Plan a Setup activation step | Deploying `status` `Active` is downgraded to `Design` |
| Existing Apex trigger handles permission assignment | Deactivate trigger, then activate the policy | Two independent writers of the same assignment rows |

---

## Recommended Workflow

1. **Confirm the feature and the permission** — check `UserManagementSettings.userAccessPoliciesEnabled` in the target org's settings metadata, and that the deploying identity holds **Manage User Access Policies**. Without the setting, the UAP-gated fields on `PermissionSetAssignment` do not exist either, so verification (step 6) has nothing to read.

2. **Write the filter before the actions** — decide the population first. Number each `userAccessPolicyFilters` row with `sortOrder`, then write `booleanFilter` over those numbers. Use `operation` `in` where a single attribute has several qualifying values; use `1 OR 2` where two different attributes qualify. Copy the shape from `references/metadata-examples.md`.

3. **Add the actions** — one `userAccessPolicyActions` element per access mechanism, each with `action`, `target` (developer name), and `type`. Grant and revoke actions belong in the same policy when they fire on the same event.

4. **Assign `order` across the whole policy set** — list every active policy that could match an overlapping population and give each a distinct integer 0–10,000, most specific lowest. Record the ranking in `templates/user-access-policies-template.md`; the `order` value is the only conflict resolution the platform offers.

5. **Run the checker** — `python3 skills/admin/user-access-policies/scripts/check_user_access_policies.py --manifest-dir force-app/main/default`. It validates `booleanFilter` against the declared `sortOrder` values, enum values, `order` uniqueness and range, and whether each action `target` resolves to something in the manifest.

6. **Deploy, then activate, then verify** — deploy with the package.xml from `references/metadata-examples.md`, set the policy to `Active` in Setup (the deployed status is `Design` regardless of what you wrote), create or update a matching test user, then run the verification SOQL over `UserAccessPolicy` and `UserAccessChange` in that same reference file.

7. **Cut over from Apex** — if a User trigger wrote the same `PermissionSetAssignment` rows, deactivate it in the same release, not after. Record the deactivation so a rollback restores both halves.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `userAccessPoliciesEnabled` confirmed true in the target org, and the deploying identity holds Manage User Access Policies
- [ ] `booleanFilter` is present and every number in it matches a `sortOrder` on a declared filter row
- [ ] Every `operation` used is supported at the org's API version (`in` needs v58.0+; `includes` and `equalsIgnoreCase` need v59.0+)
- [ ] Every action's `type` is one of the six `UserAccessPolicyActionTargetType` values and its `target` is a developer name that exists in the target org
- [ ] Filter rows with `type` `User` set `target` to `User` and populate both `columnName` and `value`
- [ ] `order` is unique across all active policies that could match an overlapping population, and within 0–10,000
- [ ] `triggerType` matches the intended event (`Create` / `Update` / `CreateAndUpdate`)
- [ ] The runbook contains a post-deploy Setup activation step, because a deployed `Active` status arrives as `Design`
- [ ] No active Apex trigger writes the same `PermissionSetAssignment` rows
- [ ] A verification query over `UserAccessChange` (or `PermissionSetAssignment.LastCreatedByChangeId`) is written and has been run against a test user
- [ ] `UserAccessPolicy` is in the deployment manifest, plus `Settings` if the feature flag is being turned on in the same release

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems. Full detail in `references/gotchas.md`:

1. **Overlapping policies do not stack** — the lowest-`order` active policy is the only one applied.
2. **A deployed `Active` policy arrives as `Design`** — activation is a separate Setup action.
3. **`booleanFilter` is required**, even for a single filter row, where its value is just `1`.
4. **The UAP-gated fields on `PermissionSetAssignment`** (`IsRevoked`, `LastCreatedByChangeId`, `LastDeletedByChangeId`) do not exist until the feature is enabled — a query written against a non-UAP org fails to compile.
5. **`UserAccessPolicy` is read-only over the API** — `describeSObjects()`, `query()`, `retrieve()` only. Authoring is Metadata API or Setup.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `.useraccesspolicy` files | One per policy, in the `useraccesspolicies` folder of the DX project; carries filters, actions, `order`, `status`, `triggerType` |
| package.xml entry | `<name>UserAccessPolicy</name>`, with `*` wildcard support in the manifest |
| Policy order register | The ranked list of active policies and their `order` values (template section) |
| Activation runbook step | Named owner and Setup step to move each deployed policy from `Design` to `Active` |
| Verification queries | SOQL over `UserAccessPolicy` (config as deployed) and `UserAccessChange` / `PermissionSetAssignment` (what the policy actually did) |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable `.useraccesspolicy` XML, package.xml, deploy order, and verification SOQL |
| `references/gotchas.md` | Diagnosing why a policy did not fire, did not activate, or lost to another policy |
| `references/examples.md` | Looking for a worked scenario close to the one in front of you |
| `references/llm-anti-patterns.md` | Reviewing UAP configuration or advice produced by an AI assistant |
| `references/well-architected.md` | Justifying UAP versus Apex, or writing up the governance tradeoffs |

---

## Related Skills

- admin/permission-set-architecture — use when designing the permission set and permission set group structure that UAP will assign; UAP is the provisioning mechanism, not the design tool
- admin/delegated-administration — use when granting non-admin users the ability to manage other users' permissions manually; distinct from automated UAP provisioning
- admin/permission-sets-vs-profiles — use when deciding whether to use profiles or permission sets as the primary access control mechanism before configuring UAP filters
- admin/permission-set-expiration — use when access should lapse on a date rather than on an attribute change
- admin/user-management — use for the surrounding user lifecycle (creation, deactivation, freeze) that UAP hooks into

---

## Official Sources Used

- Metadata API Developer Guide — `UserAccessPolicy`, `UserAccessPolicyAction`, `UserAccessPolicyFilter`, and their enumerations (field tables, `booleanFilter` OR support, `order` 0–10,000 lowest-wins, deploy-time `Active` → `Design`, sample definitions and package.xml): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `UserManagementSettings` (`userAccessPoliciesEnabled`, `enableEnhcUiUserAccessPolicies`): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — `UserAccessPolicy` and `UserAccessChange` standard objects (supported calls, field properties, access rules): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference for the Salesforce Platform — `PermissionSetAssignment` (`IsRevoked`, `LastCreatedByChangeId`, `LastDeletedByChangeId`) and `GroupMember`: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Developer Guide — "sObjects That Can't Be Used Together in DML Operations" (what MIXED_DML_OPERATION actually is): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
