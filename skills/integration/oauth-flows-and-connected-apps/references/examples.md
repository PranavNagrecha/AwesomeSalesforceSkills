# Examples - Oauth Flows And Connected Apps

## Example 1: Client Credentials For Middleware

**Context:** A middleware platform polls Salesforce for order changes every five minutes.

**Problem:** The team proposes a human admin account and password because it is quick.

**Solution:** Create a connected app for machine-to-machine access, use Client Credentials, and bind the token to a dedicated integration principal with only the required permission sets.

**Why it works:** There is no user context requirement, and the security posture is much cleaner than password-based auth.

---

## Example 2: Authorization Code For A User-Facing Portal Add-On

**Context:** A third-party application lets sales reps authorize access to their Salesforce records.

**Problem:** A server-to-server flow would lose per-user consent and authority.

**Solution:** Use Authorization Code flow and keep scopes limited to what the user-facing app truly needs.

**Why it works:** The app acts with user context instead of with a shared service principal.

---

## Anti-Pattern: Username-Password Flow As Default

**What practitioners do:** They choose username-password flow because it seems easier to script.

**What goes wrong:** Password storage, policy drift, and incident response all become harder.

**Correct approach:** Use an OAuth flow that matches the actor model and supports clean token management.
