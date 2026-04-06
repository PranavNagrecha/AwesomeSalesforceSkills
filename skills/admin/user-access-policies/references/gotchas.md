# Gotchas — User Access Policies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: UAP Does Not Backfill Existing Users on Policy Activation

**What happens:** When an admin activates a new User Access Policy, the policy does not retroactively apply to existing users who already match the filter criteria. Only users created or updated after activation are evaluated.

**When it occurs:** Any time a new UAP is activated in a live org with an existing user base. Admins who activate a Grant policy expecting all matching users to immediately receive the permission set will find no change to existing users.

**How to avoid:** After activating a new policy, run a separate data operation to apply permissions to existing users. Options include a bulk update to touch the filter field on matching users (triggering UAP re-evaluation), a Data Loader update, or a one-time permission set assignment via the Setup UI or API. Document this onboarding step in change management runbooks.

---

## Gotcha 2: Re-Evaluation Only Fires on Filter-Field Changes

**What happens:** UAP re-evaluation is triggered only when a user field that appears in an active policy's filter criteria is updated. If a user's permissions drift out of alignment (e.g., a permission set was manually removed), updating unrelated fields does not trigger re-evaluation and the drift persists.

**When it occurs:** Common in integrations that sync user data from HR systems. If the HR sync updates fields not referenced in any UAP filter (e.g., updating a phone number), no re-evaluation fires even if the user's qualifying attributes are conceptually stale.

**How to avoid:** Design filter criteria around fields that are reliably updated by provisioning workflows (Profile, Department, Role). If drift detection is needed, build a scheduled job or flow that touches the filter field for users who appear out of sync. Do not assume UAP self-heals without an update event.

---

## Gotcha 3: Revoke Policy Wins When Both Grant and Revoke Match the Same User

**What happens:** The platform evaluates all Grant policies first, then all Revoke policies. If a user matches both a Grant and a Revoke policy for the same permission set, the grant fires first and assigns the permission set, then the revoke fires and removes it. The final state is revoked.

**When it occurs:** Policy design errors where a single user segment is covered by overlapping Grant and Revoke policies targeting the same permission set. Often happens when admins create Revoke policies with broad filter criteria that unintentionally capture users already covered by a Grant policy.

**How to avoid:** Before activating policies, map out all filter criteria and identify any user segments that satisfy both Grant and Revoke conditions for the same permission set. Design filter criteria to be mutually exclusive between Grant and Revoke policies. Test conflict scenarios in sandbox with real user records before promoting to production.

---

## Gotcha 4: Existing Apex Triggers and UAP Run Simultaneously Without Coordination

**What happens:** If an Apex trigger on the User object assigns or revokes permission sets and a UAP policy targets the same permission sets for the same users, both execute on qualifying user events. This can cause MIXED_DML exceptions, duplicate assignment attempts, or conflicting outcomes depending on trigger/policy execution order.

**When it occurs:** During UAP adoption in orgs that already have Apex-based permission automation. Admins activate UAP policies without deactivating the corresponding Apex triggers, assuming the platform will coordinate them.

**How to avoid:** Before activating any UAP policy, identify and deactivate all Apex triggers that manage permission sets for the same user population. Treat UAP activation as a cutover event, not an additive step. Document the deactivated triggers in the deployment record in case rollback is needed.

---

## Gotcha 5: Custom User Field Filters Require Release 246 or Later

**What happens:** Attempting to use a custom user field as a UAP filter criterion in an org on release 242–245 will fail or the option will not appear in the policy builder. Custom fields were not supported as filter criteria until the release 246 (Spring '26) enhancement.

**When it occurs:** When a UAP design calls for filtering on a custom field (e.g., a custom `Team__c` or `Region__c` field) in an org that has not yet received the release 246 update.

**How to avoid:** Check the org's Salesforce release version before designing UAP filters that use custom user fields. For orgs on release 242–245, restrict filter criteria to standard fields: Profile, Role, UserType, and Department. If the org is scheduled for a future release, document the custom-field filter as a deferred enhancement.
