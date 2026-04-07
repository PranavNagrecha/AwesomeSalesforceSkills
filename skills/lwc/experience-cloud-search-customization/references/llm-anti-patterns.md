# LLM Anti-Patterns — Experience Cloud Search Customization

Common mistakes AI coding assistants make when generating or advising on Experience Cloud search customization. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using the Aura Search Component in an LWR Site

**What the LLM generates:** Advice to "drag the Search component from the Components panel" onto an LWR site page, or a configuration walkthrough that references the single unified "Search" component without distinguishing between LWR and Aura templates.

**Why it happens:** Training data contains Salesforce documentation and community posts from when Aura was the dominant template type. LLMs conflate the single Aura `Search` component with LWR, or they describe the generic concept of "the search component" without template-specific differentiation.

**Correct pattern:**

```
For LWR sites:
- Place "Search Bar" component in the header or hero region
- Place "Search Results" component on the search results page
- These are TWO separate components that work together

For Aura sites:
- Place the "Search" component (single Aura-based component)

Never mix components across template types.
```

**Detection hint:** Look for advice that refers to a single "Search" component without mentioning whether the site is LWR or Aura, or that does not differentiate between the two components needed on LWR sites.

---

## Anti-Pattern 2: Missing the Impact of Secure Guest User Record Access on Search

**What the LLM generates:** Guest search configuration advice that covers only object permissions and org-wide defaults (OWD), without mentioning the "Secure Guest User Record Access" org-level setting. The advice concludes with "set OWD to Public Read Only and the Guest User profile will be able to see records in search."

**Why it happens:** The Secure Guest User Record Access setting was introduced in Winter '21 and has been progressively enforced. LLMs trained on older documentation or community answers may not include this setting in their mental model of guest access. The OWD-alone mental model was correct before this setting existed.

**Correct pattern:**

```
Guest user search access requires ALL of the following:
1. Object read permission on the Guest User profile
2. OWD that permits guest access (or explicit sharing rules/sharing sets)
3. Secure Guest User Record Access setting reviewed:
   - If ENABLED (default in new orgs): explicit sharing rules required
     for every object guests should search; OWD alone is insufficient
   - If DISABLED (legacy orgs): OWD Public Read Only is sufficient
     but Salesforce recommends enabling the setting

Always test as a real guest user in an incognito session.
```

**Detection hint:** Check whether the advice mentions "Secure Guest User Record Access" by name. If it only mentions OWD and object permissions for guest search, it is incomplete.

---

## Anti-Pattern 3: Not Configuring Search Scope — Exposing Unintended Objects

**What the LLM generates:** Instructions to "enable search" on Experience Cloud that skip the Search Manager scope step, or advice that says "all searchable objects are automatically available on your site." The LLM treats the org-wide "Allow Search" setting on objects as equivalent to site-level search scope configuration.

**Why it happens:** LLMs conflate org-level search settings (Setup > Object Manager > Allow Search) with site-level search scope (Experience Builder > Search Manager). These are two separate controls. An object can be searchable org-wide but excluded from a specific site's scope.

**Correct pattern:**

```
Two separate controls govern Experience Cloud search:
1. Org-level: Setup > Object Manager > [Object] > "Allow Search"
   - Makes the object eligible to appear in Search Manager
   - Does NOT add it to any site's search scope

2. Site-level: Experience Builder > Search (Search Manager)
   - Explicitly controls which objects appear in results on THIS site
   - Must be configured per site
   - Default behavior after site creation may include all searchable objects —
     this must be reviewed and trimmed to only required objects
```

**Detection hint:** If the advice does not mention the Search Manager in Experience Builder as a separate step from enabling search on the object, the scope configuration step has been skipped.

---

## Anti-Pattern 4: Recommending SOSL for Real-Time Site Search Instead of Search Manager Configuration

**What the LLM generates:** Apex code that executes SOSL queries from a custom LWC to power the site's main search bar, presented as the standard or recommended approach for Experience Cloud search. The code includes `FIND :searchTerm IN ALL FIELDS RETURNING Knowledge__kav(...)`.

**Why it happens:** SOSL is a legitimate Apex feature and LLMs correctly know it is used for full-text search. They generalize from internal app search patterns (where custom Apex SOSL is common) to Experience Cloud, where the platform provides a declarative search infrastructure that should be used first.

**Correct pattern:**

```
For standard site search (showing a list of results when a user searches):
- Use the built-in Experience Cloud search infrastructure:
  Search Manager configures scope, Experience Builder places the
  standard search components (LWR or Aura), and the platform
  handles indexing, ranking, and result rendering.

Custom Apex SOSL is appropriate only when:
- Building a specialized search interaction that is separate from
  the site's global search (e.g., an inline search within a specific
  page component that is not the main site search)
- The standard search result layout cannot be achieved via a custom
  federatedSearchResult or uiSearchApi LWC component

For standard site-wide search, configure Search Manager and
use the platform-provided components. Do not replace the platform
search infrastructure with a custom SOSL component unnecessarily.
```

**Detection hint:** If the response proposes writing an Apex SOSL controller for the main site search bar without first considering Experience Builder's native search configuration, this anti-pattern is present.

---

## Anti-Pattern 5: Assuming Federated Search Uses a Named Credential in the Standard Apex Callout Path

**What the LLM generates:** Configuration instructions for federated search that say "create a Named Credential for the external endpoint and reference it in your Apex callout" or "add the endpoint to Remote Site Settings so Salesforce can reach it." The LLM treats federated search as if it were an Apex-initiated HTTP callout.

**Why it happens:** LLMs correctly know that Salesforce outbound HTTP callouts require Named Credentials or Remote Site Settings in the Apex context. They incorrectly apply this knowledge to federated search, which is a separate platform feature that does not use Apex for the outbound callout.

**Correct pattern:**

```
Federated search outbound calls are made by Salesforce's search
infrastructure directly, NOT by Apex:

1. The external endpoint must be reachable from Salesforce's
   outbound IP ranges (Remote Site Settings do NOT apply here)

2. Authentication is configured in:
   Setup > Federated Search > [source] > Authentication settings
   NOT in a Named Credential used for Apex

3. If the endpoint requires authentication, configure it in the
   federated search source setup in the Admin UI.

4. To verify connectivity, test the endpoint URL directly from
   Salesforce's known outbound IP addresses, not by running an
   Apex test class.
```

**Detection hint:** If the response mentions "Named Credential" or "Remote Site Settings" in the context of setting up a federated search source endpoint, the Apex callout path is being incorrectly applied. Named Credentials may legitimately appear if a custom Apex-based search proxy is being built as a supplementary integration, but they do not apply to the federated search platform feature itself.

---

## Anti-Pattern 6: Treating Admin Experience Builder Preview as Valid Guest Search Testing

**What the LLM generates:** A testing instruction that says "click Preview in Experience Builder and search for a record to verify guest access is working correctly."

**Why it happens:** LLMs correctly identify Experience Builder's preview feature as a testing tool for Experience Cloud sites. They do not distinguish between admin preview (which runs under admin credentials) and actual guest user access.

**Correct pattern:**

```
Experience Builder admin preview bypasses:
- Guest User profile permissions
- Org-wide defaults for guest users
- Secure Guest User Record Access setting
- Data category visibility for Knowledge (guest context)

Correct guest search testing:
1. Publish the site (or use the preview URL)
2. Open an incognito/private browser window
3. Navigate to the site URL without logging in
4. Perform the search
5. Verify results match expected guest user visibility
```

**Detection hint:** If testing instructions for guest search only reference Experience Builder preview and do not mention an incognito browser session, this anti-pattern is present.
