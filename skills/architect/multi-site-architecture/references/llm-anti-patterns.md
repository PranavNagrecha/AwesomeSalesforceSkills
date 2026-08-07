# LLM Anti-Patterns — Multi-Site Architecture

Common mistakes AI coding assistants make when generating or advising on multi-site Experience Cloud architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Ignoring preview and inactive sites when calculating the 100-site limit

**What the LLM generates:** Advice such as "you can create up to 100 active Experience Cloud sites per org" or "the limit is 100 live portals." The model counts only active/published sites and tells the user they have available capacity.

**Why it happens:** Training data frequently describes the limit in terms of "active sites" without explicitly stating that inactive and preview sites also consume the quota. The model generalizes from partial documentation.

**Correct pattern:**

```text
Salesforce, "How Many Experience Cloud Sites Can My Org Have?":

  "You can have up to 100 Experience Cloud sites in your org. Active,
   inactive, and preview sites, including Visualforce sites, count
   against this limit. Archived sites don't count against this limit."

Counts against the 100:      Does NOT count:
  - Active (published, live)   - Archived
  - Preview (admins only)
  - Inactive (deactivated)
  - Visualforce sites
```

Always inventory the org's total site count — not just active sites, and remembering to include Visualforce sites — before advising on capacity.

**Detection hint:** Look for "active sites" or "live portals" language without mention of preview, inactive, or Visualforce sites. Flag any capacity estimate that does not account for the full site inventory, and any inventory that counts archived sites toward the limit.

---

## Anti-Pattern 1b: Telling the user deletion is the only way to reclaim a site slot

**What the LLM generates:** "A site is only removed from the quota count when it is permanently **deleted**, not when it is deactivated. Delete obsolete sites rather than deactivating them indefinitely."

**Why it happens:** The model correctly learns the counter-intuitive half of the rule — *deactivating does not free a slot* — and then over-generalises it into an absolute. The reasoning is a false dichotomy: having established that the reversible-looking option (deactivate) fails, it concludes the irreversible one (delete) must be the answer, without checking whether a third state exists. **Archived** is that third state, and it is less represented in training data than active/inactive because it is a later-added lifecycle stage. This is a general failure shape worth naming: when a model asserts "the only way to X is Y", the assertion is usually reconstructed from a two-option mental model, and the correct answer is frequently a third option it did not enumerate.

The damage here is asymmetric and irreversible. Following this advice destroys Experience Builder configuration, page variations and audience targeting for prototypes that turn out to matter later — and it buys nothing, because archiving frees the same slot.

**Correct pattern:**

```text
To reclaim a site slot:
  Deactivate  -> does NOT free the slot   (inactive still counts)
  ARCHIVE     -> frees the slot, REVERSIBLE   <-- correct default
  Delete      -> frees the slot, PERMANENT    <-- last resort only

Recommend archiving. Recommend deletion only when the user has stated the
site will never be revived.
```

**Detection hint:** Grep generated Experience Cloud guidance for `delete` within the same sentence or bullet as `quota`, `limit`, or `slot` — and for the absolute phrasings "only way", "must be deleted", "permanently deleted" in that context. Each is a fabrication signal. More broadly, treat any recommendation of an irreversible action as requiring an explicit check that no reversible action achieves the same result; that check is cheap and this class of error is not.

---

## Anti-Pattern 2: Recommending custom domain configuration in sandbox

**What the LLM generates:** Instructions to configure a custom domain in a sandbox org as part of pre-production testing: "Go to Setup > Custom URLs in your sandbox and add the branded domain before promoting to production."

**Why it happens:** The model applies general "test in sandbox before production" best practices without knowing that custom domain configuration in Experience Cloud is a production-only operation. Salesforce documentation sometimes omits environment-specific constraints on this feature.

**Correct pattern:**
Custom domain configuration (`Setup > Custom URLs`) is only functional in production orgs. Sandbox Experience Cloud sites use the default `.sandbox.my.site.com` URL pattern. There is no way to configure a custom domain in a sandbox.

Pre-production testing must use the default sandbox URL. SSO provider configurations and CSP trusted sites for sandbox environments must reference the `.sandbox.my.site.com` URL, not the custom domain.

**Detection hint:** Any instruction to configure `Custom URLs` in a sandbox context. Any step in a sandbox runbook that references the branded custom domain URL.

---

## Anti-Pattern 3: Designing native cross-portal session sharing or automatic session hand-off

**What the LLM generates:** A solution that passes session tokens, user IDs, or authentication context via URL parameters, cookies, or hidden form fields when navigating between Experience Cloud sites — presented as a "seamless cross-portal navigation" feature.

Example wrong output:
```javascript
// WRONG — do not attempt to pass session context between sites
const targetSiteUrl = 'https://org.my.site.com/partnerportal'
    + '?sessionId=' + encodeURIComponent(userSession.sessionId)
    + '&userId=' + userId;
window.location.href = targetSiteUrl;
```

**Why it happens:** The model reasons from general web development patterns where same-origin authentication or token forwarding is a known technique. It does not know that Salesforce Experience Cloud has no supported mechanism for cross-site session sharing and that passing session tokens in URLs is a security vulnerability in the Salesforce context.

**Correct pattern:**
There is no native Salesforce capability for cross-site session transfer. The supported approach is SSO via an external IdP (Okta, Azure AD, Ping Identity) with each site registered as a separate Service Provider. The IdP maintains the active session; when the user navigates to a second site, the IdP issues a new SAML assertion transparently.

Cross-site navigation should be implemented as plain hyperlinks to the target site's URL. The authentication experience at the boundary depends on the IdP configuration.

**Detection hint:** Look for `sessionId` in URL parameters, cookie manipulation logic between sites, or Apex code that constructs URLs with authentication tokens for cross-site navigation purposes.

---

## Anti-Pattern 4: Recommending separate orgs as the default solution for portal isolation needs

**What the LLM generates:** "To keep your customer portal and your partner portal completely separate, create two separate Salesforce orgs — one for each portal. This ensures clean isolation of data and configuration."

**Why it happens:** Multi-org is a known Salesforce pattern and the model associates "isolation" with "separate orgs." It does not weigh the significant operational overhead of multi-org versus the availability of multi-site within one org as the correct pattern for most portal segregation requirements.

**Correct pattern:**
Multiple Experience Cloud sites within a single org provide audience and URL separation without cross-org complexity. The correct default for portal isolation is:
- Separate Experience Cloud sites per audience within one org
- Per-site guest user profiles for guest access control
- Record-level sharing rules and permission sets for authenticated user data access

Multi-org architecture is justified only when there is a documented requirement that a single org structurally cannot satisfy: data residency laws, M&A separation with no data overlap, or ISV tenant isolation. For portal use cases, a single org with multiple sites is almost always the correct architecture.

**Detection hint:** Any recommendation to create a new production Salesforce org for audience or portal separation without an explicit regulatory or data residency justification.

---

## Anti-Pattern 5: Hardcoding the custom domain URL in Apex, Flow, or component configuration

**What the LLM generates:** Apex code, Flow variable defaults, or component property values that hardcode the production custom domain URL (e.g., `https://portal.company.com`) without accounting for sandbox environments.

Example wrong output:
```apex
// WRONG — hardcoded production custom domain
String siteBaseUrl = 'https://portal.company.com';
String inviteUrl = siteBaseUrl + '/register?token=' + token;
```

**Why it happens:** The model generates the URL from the context provided (e.g., "our site is at portal.company.com") without flagging that this URL pattern does not work in sandbox and is not portable across environments.

**Correct pattern:**
Externalize the site base URL using environment-specific configuration:

```apex
// CORRECT — externalized via Custom Metadata
Site_Config__mdt config = [
    SELECT Base_URL__c
    FROM Site_Config__mdt
    WHERE DeveloperName = 'CustomerPortal'
    LIMIT 1
];
String siteBaseUrl = config.Base_URL__c; // sandbox: .sandbox.my.site.com; prod: portal.company.com
String inviteUrl = siteBaseUrl + '/register?token=' + token;
```

Custom Metadata allows per-environment values without code changes. The sandbox record stores the `.sandbox.my.site.com` URL; the production record stores the custom domain URL.

**Detection hint:** Literal `https://` URLs with a company domain pattern inside Apex string literals, Flow variable defaults, or hard-coded component property values. Look for the custom domain appearing directly in code rather than in configuration.

---

## Anti-Pattern 6: Assuming a single LWC component can be shared without verifying guest user profile permissions per site

**What the LLM generates:** "Deploy the shared component to your org and it will work on all your Experience Cloud sites — components are org-level resources." This is technically accurate for the deployment step but omits the critical guest user profile configuration required per site.

**Why it happens:** The model correctly understands that LWC components are org-scoped metadata and that deployment to the org makes them available in all sites' Experience Builder palettes. It does not know that runtime access to data (Apex, objects, fields) is governed by the site-specific guest user profile, not the component's presence in the org.

**Correct pattern:**
After deploying a shared LWC component to the org, verify and configure the guest user profile on each site where the component will run:

1. Navigate to `Setup > Digital Experiences > All Sites > [Site Name] > Administration > Guest User Profile`.
2. Confirm that the guest user profile has Read access to every object and field the component queries.
3. Confirm that any Apex class called by the component is included in the profile's Apex class access list (if using `without sharing` Apex).
4. Repeat for every site where the component is deployed.

Shared deployment does not imply shared runtime permissions. Guest profile configuration is always per-site.

**Detection hint:** Any deployment instruction for shared LWC components that does not include a per-site guest user profile verification step. Any assumption that component testing on Site A is sufficient to validate the same component on Site B.
