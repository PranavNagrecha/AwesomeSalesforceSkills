# LLM Anti-Patterns — Apex Custom Permissions Check

Common mistakes AI coding assistants make with Custom Permissions.

## Anti-Pattern 1: Checking user profile name instead of custom permission

**What the LLM generates:**

```
User u = [SELECT Profile.Name FROM User WHERE Id = :UserInfo.getUserId()];
if (u.Profile.Name == 'System Administrator') { ... }
```

**Why it happens:** Model reaches for the most-visible identifier.

**Correct pattern:**

```
if (FeatureManagement.checkPermission('Approve_Big_Deals')) { ... }

Profile names are fragile: renames, multiple profiles needed, non-admin
power users excluded. Custom Permissions + Permission Sets is the
platform-idiomatic gate.
```

**Detection hint:** Apex SOQL selecting `Profile.Name` for authorization decisions.

---

## Anti-Pattern 2: Using Schema.describe for custom permission check

**What the LLM generates:**

```
// Complex describe-based check via SetupEntityAccess
```

**Why it happens:** Model found an old Stack Overflow answer.

**Correct pattern:**

```
FeatureManagement.checkPermission('My_Perm') is the documented,
transaction-cached API. Avoid Schema describe workarounds — slower,
more code, no caching benefit.
```

**Detection hint:** Apex querying SetupEntityAccess or PermissionSetAssignment to determine a custom permission grant.

---

## Anti-Pattern 3: Hardcoding user Ids for bypass

**What the LLM generates:** `if (UserInfo.getUserId() == '005...') return;`

**Why it happens:** Model fixes a test scenario quickly.

**Correct pattern:**

```
Create a "Bypass_Trigger" custom permission, assign to the QA user via
Permission Set. Check via FeatureManagement.checkPermission. Now
portable, deployable, and auditable.
```

**Detection hint:** Apex comparing `UserInfo.getUserId()` to a literal Id for authorization.

---

## Anti-Pattern 4: Checking permission inside a loop

**What the LLM generates:**

```
for (Opportunity o : opps) {
    if (FeatureManagement.checkPermission('X')) { ... }
}
```

**Why it happens:** Model scatters the check defensively.

**Correct pattern:**

```
Hoist the check above the loop — permission is per-user, not per-record:
Boolean canX = FeatureManagement.checkPermission('X');
for (Opportunity o : opps) { if (canX) { ... } }
```

**Detection hint:** `FeatureManagement.checkPermission` inside a `for` or `while` block.

---

## Anti-Pattern 5: Custom Setting as user-level feature flag

**What the LLM generates:** Hierarchy Custom Setting `FeatureFlags__c` with Boolean fields per feature.

**Why it happens:** Model reaches for Custom Settings without knowing about Custom Permissions.

**Correct pattern:**

```
User-granular feature toggles belong in Custom Permissions. Custom
Settings hierarchy supports per-user overrides but is administered
separately from Permission Sets and invisible to formulas/validation
rules. Custom Permissions are the unified surface.
```

**Detection hint:** Hierarchy Custom Setting with Boolean fields named like `Has_Feature_X__c`.
