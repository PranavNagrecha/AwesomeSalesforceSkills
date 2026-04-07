# Examples — Experience Cloud API Access

## Example 1: Enabling Apex API Access for a Customer Community Plus User

**Context:** A B2B self-service portal uses Customer Community Plus licenses. The company wants a mobile app to call the Salesforce REST API using the portal user's credentials so the app can retrieve open cases and account data scoped to that user's account.

**Problem:** The initial attempt to call `/services/data/v60.0/query/?q=SELECT+Id,Subject+FROM+Case` returns a `403 Forbidden` with the error `API_DISABLED_FOR_ORG`. The developer suspects a permission set is missing.

**Solution:**

Step 1 — Confirm the license. Customer Community Plus supports API access. Customer Community does not. Verify the user's license in Setup > Users > [user record] > License.

Step 2 — Enable "API Enabled" on the external profile. In Setup > Profiles > [Customer Community Plus User profile] > System Permissions, enable "API Enabled". This permission is off by default for all external profiles.

Step 3 — Create a Connected App with `api` scope. Do not grant `refresh_token` unless the app needs offline access. Do not grant `full`.

Step 4 — Verify external OWDs. In Setup > Sharing Settings, check the "External Access" column for the Case object. If it reads "Private", the REST API query will return zero rows even for the user's own cases unless a Sharing Set grants access. Add a Sharing Set (Setup > Digital Experiences > Settings > Sharing Sets) that maps `User.AccountId` to `Case.AccountId`.

Step 5 — Test with the actual community user credential using the OAuth 2.0 Username-Password flow for a server-side app, or the Web Server flow for an interactive app. Confirm cases for the user's account are returned and cases for other accounts are not.

```apex
// This is what the platform enforces server-side — no Apex needed for a direct REST call.
// The sharing model (external OWDs + Sharing Set) is what controls the result set.
// Verify with SOQL in anonymous Apex run as the community user (not a sysadmin):
System.runAs(communityUser) {
    List<Case> cases = [SELECT Id, Subject FROM Case WITH USER_MODE];
    System.debug(cases.size()); // Should match only cases on the user's account
}
```

**Why it works:** Customer Community Plus license includes API entitlement. "API Enabled" unlocks that entitlement at the profile level. External OWDs plus a Sharing Set ensure the REST API query returns only the records the user is supposed to see. Testing as the actual user (not sysadmin) is the only reliable way to confirm the sharing model is correct.

---

## Example 2: Guest User Apex Data Access with Sharing Enforcement

**Context:** An e-commerce Experience Cloud site has a public product catalog page. An LWC component calls an Apex method to retrieve active products. After a security review, the team needs to confirm guest users cannot access pricing data from the Opportunity or Order objects.

**Problem:** The Apex class was originally written `without sharing` because a developer wanted to ensure all products were always visible. This means the class runs in system context, bypassing the guest profile entirely. If the query were ever changed or extended, it could inadvertently expose sensitive records.

**Solution:**

Step 1 — Change the Apex class declaration from `without sharing` to `with sharing`.

Step 2 — Audit the guest profile (Setup > Users > [site guest user] > Edit). Remove all object permissions and FLS except the minimum needed: `Product2` object with Read access, and only the `Name`, `Description`, and `IsActive` fields readable.

Step 3 — Set the external OWD for `Product2` to "Public Read Only" in Setup > Sharing Settings so guest users can reach product records through the sharing model.

Step 4 — Explicitly check FLS before reading fields in the Apex class.

Step 5 — Confirm `Opportunity` and `Order` objects have no object-level read permission on the guest profile, and their external OWDs are "Private". An unintended query against these objects will return zero rows.

```apex
public with sharing class GuestProductController {
    @AuraEnabled(cacheable=true)
    public static List<Product2> getActiveProducts() {
        // Confirm field accessibility before using in query
        if (!Schema.sObjectType.Product2.fields.Name.isAccessible()
            || !Schema.sObjectType.Product2.fields.Description.isAccessible()) {
            throw new AuraHandledException('Insufficient field access for product catalog.');
        }
        return [
            SELECT Id, Name, Description
            FROM Product2
            WHERE IsActive = true
            WITH USER_MODE
        ];
    }
}
```

**Why it works:** `with sharing` ensures Apex respects the guest user's sharing context. `WITH USER_MODE` in SOQL enforces FLS and CRUD at the query level — it is the declarative enforcement complement to the programmatic `Schema.sObjectType` check. The external OWD and guest profile permissions together mean `Opportunity` and `Order` records are unreachable even if the query were modified.

---

## Anti-Pattern: Using a System Administrator Integration User for Community API Access

**What practitioners do:** Rather than configuring API access for the community user, a developer creates a Connected App that uses a System Administrator integration user credential. The community app server-side calls the Salesforce API as the sysadmin and filters results by account ID in application code.

**What goes wrong:** The application code filtering is fragile and error-prone. Any bug or regression in the filter logic exposes all records in the org to the portal user. The platform sharing model — which is audited, enforced at the database level, and tested — is bypassed entirely. Salesforce security reviews and ISV reviews will flag this pattern as a critical finding. It also grants the integration user excessive privileges that become an attack surface.

**Correct approach:** Use the community user's own credential for API calls (Customer Community Plus or Partner Community). Configure external OWDs and Sharing Sets so the platform enforces record visibility. For Customer Community licenses (which have no API entitlement), use a mid-tier service that makes the API call as an integration user but applies server-side filtering validated against the community user's account context — and document this as a known architectural tradeoff, not a preferred pattern.
