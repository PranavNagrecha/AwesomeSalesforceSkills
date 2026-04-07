# LLM Anti-Patterns — Experience Cloud API Access

Common mistakes AI coding assistants make when generating or advising on Experience Cloud API access.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending REST API Access for a Customer Community License User

**What the LLM generates:** Instructions to enable "API Enabled" in the Customer Community user profile, create a Connected App, and configure OAuth so the community user can call the Salesforce REST API directly.

**Why it happens:** LLMs conflate "Experience Cloud user" with "Salesforce user with external access" and assume all profile permission problems are solvable with the right permission set or profile flag. They do not distinguish between license tier entitlements that are platform-enforced vs. permission configuration that is admin-controlled.

**Correct pattern:**

```
Customer Community license does not include REST/SOAP API access.
This is a license-level platform restriction — no profile or permission set change resolves it.
Options:
  1. Upgrade to Customer Community Plus or Partner Community license.
  2. Use a server-side mid-tier integration with a separate integration user credential.
  3. Use LWC components with @AuraEnabled Apex for on-page data access (does not require API entitlement).
```

**Detection hint:** Any suggestion to enable "API Enabled" or configure OAuth for a user confirmed to hold a Customer Community (non-Plus) license should be flagged.

---

## Anti-Pattern 2: Ignoring FLS on the Guest Profile and Relying Solely on Permission Sets

**What the LLM generates:** A recommendation to create a permission set that grants read access to a set of fields and assign it to the guest user, then call those fields in an Apex query without checking the guest profile's FLS.

**Why it happens:** Permission sets are the standard mechanism for managing field access for internal users. LLMs generalize this to guest users without knowing that guest user FLS is controlled exclusively on the guest profile, not via permission sets (which grant class access for guest users, not field access).

**Correct pattern:**

```
Guest user field access is configured on the guest profile directly:
Setup > Users > [Site Guest User] > Edit > Field Permissions

Permission sets cannot override guest profile FLS.
Always check:
  Schema.sObjectType.Object.fields.FieldName.isAccessible()
before using a field in a guest-accessible Apex query.
```

**Detection hint:** Any recommendation to assign a permission set to grant field access to a guest user, without a corresponding instruction to also configure the guest profile's FLS, is likely wrong.

---

## Anti-Pattern 3: Writing Guest-Accessible Apex `without sharing`

**What the LLM generates:** An Apex class intended for an Experience Cloud guest page, declared `without sharing` (or not explicitly declared, which in a context inheriting from a `without sharing` class defaults to system mode).

**Why it happens:** LLMs often default to `without sharing` or omit the sharing keyword when demonstrating "make all data visible" scenarios. In internal contexts this is a performance or access shortcut. In a guest user context it is a security violation that exposes the entire org.

**Correct pattern:**

```apex
// WRONG — do not use for guest-accessible endpoints
public without sharing class GuestController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getAccounts() { ... }
}

// CORRECT
public with sharing class GuestController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getAccounts() {
        return [SELECT Id, Name FROM Account WITH USER_MODE];
    }
}
```

**Detection hint:** Any `@AuraEnabled` class for an Experience Cloud page that is declared `without sharing` or that omits the sharing keyword should be flagged as a potential security issue.

---

## Anti-Pattern 4: Granting Overly Broad OAuth Scopes to External User Connected Apps

**What the LLM generates:** A Connected App configuration that grants `full` scope (or `full refresh_token`) to a Customer Community Plus or Partner Community user integration, on the assumption that broader scope ensures the integration works.

**Why it happens:** LLMs associate `full` scope with "everything works" and `api` scope with "limited functionality". In practice, `api` scope covers all data API calls for an external user. `full` additionally includes profile access, admin APIs, and other capabilities that external portal users should never have.

**Correct pattern:**

```
For external user REST API integrations:
  Minimum scope: api
  Add refresh_token only if the app needs offline (non-interactive) access
  Do not use: full, admin, web, visualforce

OAuth scope is set in the Connected App definition:
Setup > App Manager > [Connected App] > Edit > OAuth Settings > Selected OAuth Scopes
```

**Detection hint:** Any Connected App recommendation that includes `full` scope for an Experience Cloud external user integration should be flagged.

---

## Anti-Pattern 5: Assuming External OWD Visibility Matches Internal OWD Visibility

**What the LLM generates:** Advice that setting an object's internal OWD to "Public Read Only" will make records visible to external portal users, or conversely that a tight internal OWD automatically protects records from external access.

**Why it happens:** LLMs learn from documentation that OWDs control record visibility and generalize the concept without distinguishing the internal vs. external OWD rows. The external OWD is a separate, independently configurable row in Setup > Sharing Settings that was added specifically to let admins set different visibility rules for external vs. internal users.

**Correct pattern:**

```
Internal OWD and external OWD are independently configured.
An object can have:
  Internal OWD: Public Read/Write
  External OWD: Private

Changing internal OWD does not change external OWD.
To expose records to external users:
  1. Set the external OWD in Setup > Sharing Settings (the "External Access" column)
  2. Configure Sharing Sets for record-level access tied to user-account relationships
  3. Use Share Groups to extend access to users in the same portal
```

**Detection hint:** Any recommendation about external user data access that only references the internal OWD setting (or only says "set OWD to Public Read Only" without specifying the external row) is likely incomplete.

---

## Anti-Pattern 6: Using a High-Privilege Integration User to Proxy for Customer Community API Access

**What the LLM generates:** A server-side integration architecture where a System Administrator or high-privilege internal user credential is used to call the Salesforce API on behalf of a Customer Community portal user, with application-layer code filtering results by account ID.

**Why it happens:** LLMs often default to integration user patterns (a known, simple approach) when the license constraint prevents the direct approach. They do not flag the security implications of bypassing platform-enforced sharing with application-level filtering.

**Correct pattern:**

```
If Customer Community license prevents direct API access and a license upgrade is not possible:
  - Use a dedicated integration user with the minimum required permissions (not sysadmin)
  - The integration service must enforce the community user's account-scoping in its query WHERE clause
  - Document this as a compensating control with an explicit security review
  - The integration user should use IP allowlisting and certificate-based authentication
  - This is a known architectural tradeoff, not a preferred pattern

Preferred pattern: Upgrade to Customer Community Plus or Partner Community.
```

**Detection hint:** Any recommendation to use a sysadmin or broadly privileged integration user as a proxy for portal user data access, without flagging the security tradeoff and requiring a compensating control review, should be flagged.
