# LLM Anti-Patterns — License Optimization Strategy

Common mistakes AI coding assistants make when generating or advising on Salesforce license optimization. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming That Freezing a User Releases the License

**What the LLM generates:** "To recover license seats from inactive users, freeze them using `UserLogin.IsFrozen = true`. This will free up the license for reassignment."

**Why it happens:** LLMs associate "preventing login access" with "releasing the resource." The distinction between blocking access (freeze) and deallocating the license (deactivate) is a Salesforce-specific nuance that does not have a strong training-data signal.

**Correct pattern:**

```
Freezing a user (UserLogin.IsFrozen = true) blocks their login but DOES NOT release the license seat.
To recover a license seat, deactivate the user: set User.IsActive = false.
Use freeze as a temporary hold/notification step before deactivation — not as a reclamation action.
```

**Detection hint:** Any response that says "freeze" and "recover license" or "free up seat" in the same sentence without the deactivation step is wrong.

---

## Anti-Pattern 2: Advising That License Type Can Be Changed Directly on the User Record

**What the LLM generates:** "To change a user from a Salesforce CRM license to a Salesforce Platform license, go to the user record and update the License Type field."

**Why it happens:** LLMs reason by analogy — many SaaS platforms allow direct license-type changes on a user account. Salesforce's profile-bound license model is not an obvious design.

**Correct pattern:**

```
There is no editable License Type field on the User record.
A user's license type is determined by their assigned Profile.
Each Profile is bound to a specific User License (set when the profile is created).
To change a user's license type:
1. Create (or clone) a Profile bound to the target license type.
2. Validate the profile in sandbox.
3. Assign the new profile to the user in production.
```

**Detection hint:** Any response that references editing a "license" field directly on the User record is incorrect.

---

## Anti-Pattern 3: Using Only LastLoginDate to Identify Inactive Users

**What the LLM generates:** "Query `SELECT Id FROM User WHERE IsActive = true AND LastLoginDate < LAST_N_DAYS:90` to find all inactive users safe to deactivate."

**Why it happens:** `LastLoginDate` is the most obvious field for identifying inactive users and appears frequently in Salesforce developer documentation. LLMs do not know that it only stores the most recent login timestamp, not frequency.

**Correct pattern:**

```soql
-- Supplement LastLoginDate with a frequency count from LoginHistory:
SELECT UserId, COUNT(Id) loginCount
FROM LoginHistory
WHERE LoginTime = LAST_N_DAYS:90
GROUP BY UserId
HAVING COUNT(Id) < 2
```

Use `LastLoginDate` as a first-pass filter, then cross-reference with `LoginHistory` frequency for users near the threshold before recommending deactivation.

**Detection hint:** Responses that use `LastLoginDate` as the sole reclamation criterion without mentioning `LoginHistory` are incomplete for any high-stakes reclamation decision.

---

## Anti-Pattern 4: Recommending PSL Removal Without Checking Dependent Automations

**What the LLM generates:** "To recover PSL seats, query users with PSL assignments who haven't logged in for 90 days and remove their PSL assignments in bulk."

**Why it happens:** The query-and-bulk-remove pattern is straightforward and the LLM applies it without considering that PSL-gated features may be used by automations (flows, batch jobs, integrations) running under the affected user, not just by interactive logins.

**Correct pattern:**

```
Before removing any PSL assignment:
1. Check whether the user is an integration user (API-only session policy, named credentials).
2. Query FlowDefinitionView and ScheduledJob for references to the user.
3. Confirm with application owners that the PSL-gated feature is genuinely unused.
4. Schedule removal during a maintenance window.
Only then remove the PSL assignment.
```

**Detection hint:** Any bulk PSL removal recommendation that does not mention checking for integration users, scheduled jobs, or flows is incomplete.

---

## Anti-Pattern 5: Treating the REST /limits Endpoint as the Source of License Count Data

**What the LLM generates:** "Use the REST API `/services/data/vXX.0/limits` endpoint to retrieve your org's license usage and available seats."

**Why it happens:** The `/limits` endpoint is well-documented and commonly used for API monitoring. LLMs conflate "org limits" with "license limits" because both are framed as ceiling-vs-consumption data.

**Correct pattern:**

```soql
-- License seat counts live in sObjects, not the /limits endpoint:

-- Total user license seats by type:
SELECT Name, TotalLicenses, UsedLicenses FROM UserLicense

-- PSL seats:
SELECT DeveloperName, TotalLicenses, UsedLicenses FROM PermissionSetLicense

-- Per-user PSL assignments:
SELECT PermissionSetLicense.DeveloperName, AssigneeId, Assignee.Name
FROM PermissionSetLicenseAssign
```

**Detection hint:** Any advice to query license seat counts from the `/limits` REST endpoint is incorrect.

---

## Anti-Pattern 6: Assuming Login-Based License Overage Is Capped or Results in Lockout

**What the LLM generates:** "If your Login-Based License allocation is exceeded, additional users will be locked out until the next month." OR "LBL overage is automatically capped at the contracted allocation."

**Why it happens:** Many subscription systems lock out users when quotas are exceeded. LLMs apply this pattern to Salesforce LBL without knowledge of the specific Salesforce billing model.

**Correct pattern:**

```
Salesforce Login-Based License overage is NOT capped and does NOT trigger lockout.
Users continue to be able to log in after the monthly allocation is exceeded.
Overage is billed at the contracted per-login overage rate.
Orgs must monitor LBL consumption proactively via Setup > Login-Based License Usage
and set internal alerts before the allocation is exhausted each month.
```

**Detection hint:** Any response that says LBL users will be "locked out" or that overage is "capped" is incorrect.
