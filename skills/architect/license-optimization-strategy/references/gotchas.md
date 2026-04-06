# Gotchas — License Optimization Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Freezing a User Does Not Recover the License Seat

**What happens:** When a user is frozen via `UserLogin.IsFrozen = true`, their login access is blocked — but the Salesforce license they are assigned to remains consumed. The license seat count in Setup > Company Information does not decrease. Teams that freeze users as a cost-recovery measure without subsequently deactivating them see no reduction in their used-license count.

**When it occurs:** Any time an admin or script sets `IsFrozen = true` as the final step rather than as a temporary hold before deactivation. This is a very common mistake in automated offboarding scripts that stop at the freeze step.

**How to avoid:** Treat freeze as a 14-day hold step only. After the notification/grace period, deactivate the user (`User.IsActive = false`) to release the seat. Monitor seat recovery by comparing the Setup > Company Information user count before and after deactivation batches.

---

## Gotcha 2: Profiles Are Bound to a Specific License Type — Changing the License Requires a New Profile

**What happens:** A Salesforce user's license type is determined by their profile, not by a direct field on the User record. Each profile is created under a specific User License (visible in the profile's User License field). You cannot assign a profile created under the "Salesforce" license to a user who should be on the "Salesforce Platform" license — the system will throw a validation error. Many admins attempt to change a user's license type by editing the User record directly and are surprised to find no editable license field.

**When it occurs:** During license right-sizing migrations when no Platform-compatible version of the target profile exists. Affects both manual profile changes and data loader migrations.

**How to avoid:** Before any license downgrade migration, identify which profiles the target users are assigned to and whether Platform-compatible counterparts exist. If not, clone the existing profile, change the User License on the clone to "Salesforce Platform," validate object permissions (any standard CRM objects will need to be removed), test in sandbox, then use the cloned profile in production.

---

## Gotcha 3: LastLoginDate Does Not Reflect Login Frequency — Only the Most Recent Login

**What happens:** `User.LastLoginDate` stores the timestamp of the user's most recent successful login. A user who logged in yesterday but had not logged in for 11 months before that will show a recent `LastLoginDate`. Conversely, a very active user who happened to be on leave last week has a recent login date. Using `LastLoginDate` alone as a proxy for user activity produces both false negatives (recently returned users flagged as active) and false positives (formerly-active users who happened to log in once recently).

**When it occurs:** In cost audits that query only `LastLoginDate < LAST_N_DAYS:90` without supplementing with login frequency data from `LoginHistory`. This is particularly problematic when justifying a license reclassification to the business — "this user logged in last Tuesday" is a valid objection to a 90-day inactive flag.

**How to avoid:** For high-confidence reclamation decisions, supplement `LastLoginDate` with a `LoginHistory` frequency count: query the number of logins in the trailing 90 days. Users with zero or one login in 90 days despite a recent `LastLoginDate` are genuine candidates for review. `LoginHistory` records are retained for 6 months by default.

---

## Gotcha 4: Login-Based License Overage Is Billed Without a Cap or Lockout

**What happens:** When an org's monthly Login-Based License allocation is exhausted, Salesforce does not lock out additional users — it allows continued access and charges overage at the contracted per-login overage rate. There is no automatic warning, no throttle, and no ceiling. An LBL user population that grows unexpectedly (e.g., a partner recruitment campaign) can generate a materially larger invoice than budgeted.

**When it occurs:** When the LBL monthly allocation is sized against historical usage without accounting for growth events. Also occurs when seasonal spikes (e.g., annual sales kickoff, holiday promotion period) push login volume above the typical monthly baseline.

**How to avoid:** Monitor LBL consumption via Setup > Login-Based License Usage and set an internal alert when consumption reaches 80% of the monthly allocation. Review LBL allocations quarterly and adjust contracted allocation before anticipated growth events. Do not assume LBL consumption is bounded by the purchased allocation.

---

## Gotcha 5: PSL Removal Is Immediate — Active Sessions and Integrations Are Affected Instantly

**What happens:** Removing a Permission Set License assignment from a user takes effect immediately. If the user has an active browser session, PSL-gated features (e.g., Einstein Analytics dashboards, Flow Orchestration work items) become inaccessible mid-session, which produces confusing error messages. More critically, if an integration user or a scheduled flow depends on a PSL-gated feature and the PSL is removed, the automation fails immediately — there is no grace period or deferred removal.

**When it occurs:** During bulk PSL reclamation operations run during business hours. Also occurs when PSLs are unassigned from integration-user records without first confirming whether those users run any automations that require the PSL-gated feature.

**How to avoid:** Schedule PSL unassignment during off-peak maintenance windows. Before unassigning any PSL, query `FlowDefinitionView` and scheduled flows for references to the affected user. Check whether the user is an integration user by looking for API-only session policies or named credentials. Confirm with application owners that the PSL-gated feature is genuinely unused before removing.

---

## Gotcha 6: The REST /limits Endpoint Does Not Return License Seat Counts

**What happens:** The REST API `/services/data/vXX.0/limits` endpoint returns governor limit consumption (daily API requests, bulk API limits, etc.) but does not return user license seat counts or PSL assignments. Teams that build automated license dashboards against this endpoint find it does not contain the data they need and fall back to manual Setup UI checks.

**When it occurs:** When engineers attempt to automate license monitoring using the standard Limits API, which is the natural first thing to try.

**How to avoid:** License counts and PSL data live in the `UserLicense`, `PermissionSetLicense`, and `PermissionSetLicenseAssign` sObjects, which are queryable via SOQL through the standard REST query endpoint. For org-level license allocation, query `UserLicense` and `PermissionSetLicense`. For per-user assignments, query `PermissionSetLicenseAssign`. Build monitoring dashboards against these objects, not the `/limits` endpoint.
