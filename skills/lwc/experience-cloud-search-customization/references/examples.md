# Examples — Experience Cloud Search Customization

## Example 1: Configuring a Knowledge-Only Search Scope for a Self-Service Portal

**Context:** A financial services company has an Experience Cloud site (LWR template) for customer self-service. The site contains Knowledge articles, but the Search Manager currently includes Cases, Contacts, and several custom objects. Authenticated customers are accidentally seeing search results for Cases they should not be aware of, and the support team wants to lock search down to Knowledge only.

**Problem:** The Search Manager scope was left at its default (all objects with search enabled), which exposed objects that are inappropriate for customer-facing search. Customers see "0 results" on most objects due to sharing restrictions, which makes the search experience feel broken, and they occasionally see case titles from unrelated accounts due to misconfigured sharing.

**Solution:**

```
Step 1 — Open Experience Builder for the site.
Step 2 — Navigate to Search (the magnifying-glass icon in the left panel).
Step 3 — In the Search Manager, open the "Search Results" object list.
Step 4 — Remove all objects except Knowledge from the searchable objects list.
Step 5 — Confirm Knowledge has "Allow Search" enabled:
         Setup > Object Manager > Knowledge > Search Layouts
         The "Search Results" layout should include Title, Summary, and Article Number.
Step 6 — In the Search Manager, add promoted terms for the top 5 known high-volume queries
         (e.g., "how to reset password" → promote the "Password Reset" article).
Step 7 — Publish the site changes.
Step 8 — Test in an incognito browser session (guest user) and as an authenticated customer.
         Confirm only Knowledge results appear.
```

**Why it works:** Search Manager scope is per-site and declarative. Removing non-Knowledge objects from scope means the search index never considers those objects for this site's queries, regardless of org-wide searchability settings. Promoted terms ensure the most critical articles surface immediately without requiring users to know exact titles.

---

## Example 2: Federated Search Combining Salesforce Knowledge and an External Knowledge Base

**Context:** A technology company runs an Experience Cloud portal (Aura template) for partner support. Salesforce Knowledge contains internal best practice articles, but the company also maintains a Confluence wiki with hundreds of setup guides. Partners want a single search bar that returns results from both systems.

**Problem:** Without federated search, partners must search Salesforce and Confluence separately. There is no practical way to replicate Confluence content into Salesforce without significant ongoing synchronization work.

**Solution:**

```
Step 1 — Build (or deploy) an external HTTP endpoint that implements the
         Salesforce Federated Search specification. The endpoint must:
         - Accept POST requests at the registered URL
         - Parse the Salesforce search query payload (JSON with "query" field)
         - Query Confluence using its REST API
         - Return results in the Salesforce Federated Search response schema:
           {
             "items": [
               {
                 "title": "Article Title",
                 "url": "https://confluence.example.com/...",
                 "description": "Short summary text",
                 "type": "KnowledgeArticle"
               }
             ]
           }

Step 2 — Register the endpoint in Salesforce:
         Setup > Federated Search > New
         - Name: "Confluence Knowledge Base"
         - Endpoint URL: https://search-proxy.example.com/federated
         - Authentication: Named Credential (preferred) or API Key header

Step 3 — In Experience Builder > Search Manager, enable the Confluence federated
         source for this site.

Step 4 — (Optional) Create a custom federatedSearchResult LWC if the default
         result card layout is insufficient:
         - The component receives the federated result item as a property
         - Render title, description, and a link to the external URL
         - Deploy to the org and register it in the federated source configuration

Step 5 — Test by searching for a term that exists in Confluence but not in
         Salesforce Knowledge. Confirm external results appear alongside
         Salesforce results.

Step 6 — Test with the external endpoint deliberately offline to confirm
         Salesforce-native results continue to appear (external failure should
         not break native search).
```

**Why it works:** Salesforce's search infrastructure sends the user's query to the registered external endpoint at query time. The external results are merged into the native result set client-side. The external system is queried live, so there is no synchronization lag — the result reflects the current state of Confluence at search time. Using a Named Credential for authentication keeps credentials out of the endpoint URL and out of Experience Builder configuration.

---

## Anti-Pattern: Placing the Aura Search Component on an LWR Site

**What practitioners do:** A developer working on an LWR site searches the Experience Builder component panel for "Search," finds the Aura-based `Search` component (which appears in the panel even for LWR sites in some org configurations), drags it onto a page, and saves. The component appears to save successfully.

**What goes wrong:** The Aura `Search` component does not render on LWR pages at runtime. Site visitors see either an empty region where the search bar should be or a generic "component not supported" placeholder. Because the component saves without an error in Experience Builder, the developer does not discover the problem until testing the live site.

**Correct approach:** For LWR sites, use the LWC-based `Search Bar` component (for the input) and the `Search Results` component (for the results page). These are separate components that must both be placed. The `Search Bar` goes in the header or a top-of-page region; the `Search Results` component goes on a dedicated search results page. Confirm the site template type in the Experience Builder site settings before placing any search components.
