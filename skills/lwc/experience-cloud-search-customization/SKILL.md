---
name: experience-cloud-search-customization
description: "Use this skill when configuring or extending search on an Experience Cloud site — covering Search Manager scope configuration, LWR vs Aura search component selection, federated search setup, guest user search access, and custom search result components. NOT for SOSL/SOQL query development. NOT for internal Salesforce global search or Einstein Search for agents."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
triggers:
  - "How do I customize search in Experience Cloud to only show Knowledge articles?"
  - "How do I set up federated search on a community portal to pull results from an external knowledge base?"
  - "Search scope configuration in Experience Builder site builder"
  - "Community search results component not returning expected records"
  - "Cross-site search Experience Cloud guest users see wrong results"
tags:
  - experience-cloud
  - search
  - federated-search
  - lwr
  - aura
  - search-scope
  - guest-user
  - search-manager
inputs:
  - "Site type: LWR (Enhanced LWR) or Aura (legacy Aura/Visualforce hybrid)"
  - "Objects that should be searchable on the site"
  - "Whether guest (unauthenticated) users need search access"
  - "Whether external content must be merged into search results (federated search)"
  - "Current Secure Guest User Record Access org setting value"
outputs:
  - "Search Manager configuration (object scope, promoted terms)"
  - "Correct standard search component selected and placed for the site type"
  - "Federated search endpoint configuration and result mapping"
  - "Guest user sharing and Secure Guest User Record Access checklist"
  - "Custom search result component skeleton for LWR sites (if needed)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud Search Customization

Use this skill when a practitioner needs to configure, extend, or troubleshoot search behavior on an Experience Cloud site — including controlling which objects appear in results, enabling federated search against external endpoints, selecting the right standard search components for the site template type, or diagnosing guest user search visibility problems.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Site template type**: Determine whether the site is built on the LWR (Lightning Web Runtime) template, such as Build Your Own (LWR) or the newer Enhanced LWR, or the legacy Aura template (Customer Service, Partner Central, etc.). The standard search components are different and are NOT interchangeable between templates.
- **Guest user search requirement**: Determine whether unauthenticated guest users need to see search results. If yes, confirm the org-level "Secure Guest User Record Access" setting in Setup > Sharing Settings and the Guest User profile's object permissions. This setting silently restricts what guests can find regardless of sharing rules.
- **Objects to expose in search**: Identify which objects the site owner wants searchable. All objects must have "Allow Search" enabled in their object settings (Setup > Object Manager > [Object] > Search Layouts) and must be included in the site's Search Manager scope.
- **Federated search requirement**: If the request involves pulling results from an external system (a third-party knowledge base, a document management system, or another Salesforce org), identify the external endpoint URL, the authentication mechanism, and the expected result schema.

---

## Core Concepts

### Search Manager and Search Scope

Every Experience Cloud site has a Search Manager accessible from Experience Builder > Search. The Search Manager controls:

- **Which objects are searchable** on that specific site. Adding or removing objects here changes scope only for that site, not org-wide.
- **Promoted search terms**: Keywords that force specific records to appear at the top of results.
- **Search filters**: Per-object filter fields exposed to site users.

Objects must satisfy two requirements before they can be added to Search Manager scope: (1) the object must have "Allow Search" enabled in Setup, and (2) the object must have at least one field indexed for search. If an object does not appear in Search Manager's available objects list, check both of these prerequisites.

Search scope is per-site. The same object can have different search visibility on different sites in the same org.

### LWR vs Aura Search Components

Salesforce provides separate standard search components for each site template type:

| Template | Standard search component | Where it lives in Experience Builder |
|---|---|---|
| Aura sites (legacy) | `Search` component (Aura-based) | Components > Search |
| LWR sites | `Search Results` and `Search Bar` components (LWC-based) | Components panel |

These components are NOT interchangeable. Dropping the Aura `Search` component into an LWR page will silently fail or not render. Dropping the LWR `Search Results` component into an Aura site is not supported. Confirm the site template type first; then select only the matching component.

For LWR sites, Salesforce also supports building a fully custom search result component using the `lightning/uiSearchApi` wire adapter (available in API 55+), which allows custom result layouts without replacing the underlying search index.

### Federated Search

Federated search allows an Experience Cloud site to send the user's search query to an external HTTP endpoint and merge the external results with native Salesforce results in a single result set. Key mechanics:

- The external endpoint is configured in Setup > Federated Search and must accept a POST request with a specific JSON schema (the Salesforce Federated Search specification).
- The endpoint must be publicly reachable from Salesforce servers or accessible via Named Credentials if authentication is required.
- Federated search results are merged client-side using a standard result card layout; custom result layouts for federated results require a custom `federatedSearchResult` component.
- There is no Apex callout involved in federated search at runtime — Salesforce's search service makes the callout directly to the external endpoint. The external endpoint must respond within the platform's timeout window.
- Each org supports a limited number of federated search configurations; check the current governor limit for federated search sources.

### Guest User Search and Secure Guest User Record Access

Guest users (unauthenticated site visitors) execute all queries under a shared Guest User record. Two layers control what they can see in search results:

1. **Object-level sharing**: The Guest User profile must have read access on the objects being searched. Org-wide defaults for those objects must permit guest access, or sharing rules must explicitly grant it.
2. **Secure Guest User Record Access** (org setting in Setup > Sharing Settings): When this setting is enabled — and Salesforce has been gradually enforcing it as the default — guest users can only see records they own or that are explicitly shared with the Guest User via sharing rules. Records that authenticated users can see through role hierarchy or manual sharing are NOT automatically visible to guests. Enabling this setting can silently break previously working guest search results.

These two layers are independent. A guest user with object read permission but no record-level sharing access will see zero search results for that object with no error message.

---

## Common Patterns

### Pattern: Knowledge-Only Search Scope

**When to use:** A self-service portal where site visitors should search only Salesforce Knowledge articles, not Cases, Contacts, or other internal objects.

**How it works:**

1. In Experience Builder, open the Search Manager.
2. Remove all objects except `Knowledge` from the searchable objects list.
3. Ensure the Knowledge object has `IsVisibleInPkb = true` for published articles and that Guest User data category visibility is configured (see `lwc/knowledge-article-lwc` for data category details).
4. Place the appropriate search component for the site template (Aura `Search` or LWR `Search Bar` + `Search Results`).
5. If promoted terms are needed, configure them in Search Manager > Promoted Search Terms.

**Why not the alternative:** Leaving all objects in scope exposes Cases, Contacts, and custom objects in search results. Guest users who lack sharing access will see zero results for those objects, but authenticated site members may see records the business did not intend to expose. Scoping to Knowledge alone eliminates this risk.

### Pattern: Federated Search Combining Salesforce and External Knowledge Base

**When to use:** A portal where users should see results from both Salesforce Knowledge and an external knowledge base or document management system in a single search experience.

**How it works:**

1. Build or deploy an external HTTP endpoint that implements the Salesforce Federated Search specification. The endpoint must accept a POST request with the query payload and return results in the required JSON schema.
2. In Setup > Federated Search, register the endpoint URL and any required authentication (Named Credential or API key header).
3. In Experience Builder > Search Manager, enable the federated search source for the site.
4. (Optional) Create a custom `federatedSearchResult` LWC to control the layout of external results in the result list.
5. Test the integration by running a search that matches known content in the external system and confirming both Salesforce and external results appear in the merged result set.

**Why not the alternative:** Replicating external content into Salesforce as CMS content or Knowledge articles to enable native indexing is valid but creates data duplication and synchronization overhead. Federated search avoids duplication by querying the external system at search time.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Site built on LWR template, need standard search UI | Use LWC `Search Bar` + `Search Results` standard components | Aura search component is not supported on LWR pages |
| Site built on Aura template, need standard search UI | Use Aura `Search` standard component | LWR search components are not available in Aura sites |
| Need custom result card layout on LWR | Build custom LWC using `lightning/uiSearchApi` wire adapter | Allows custom layout while retaining the native search index and scope |
| Guest users not seeing expected records in search | Check Secure Guest User Record Access setting + guest sharing rules | This setting overrides object-level permissions and silently returns zero results |
| Merging external content into site search | Federated search via Setup > Federated Search + external endpoint | Avoids data duplication; real-time query to external system |
| Restricting which objects appear in search | Configure Search Manager scope in Experience Builder | Per-site control; does not affect other sites or the internal app |
| Promoting specific records for key terms | Use Promoted Search Terms in Search Manager | Declarative; no custom code required |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm site template type and search requirements**: Identify whether the site is LWR or Aura. Determine the target objects for search, whether guests need access, and whether federated (external) search is required. Document the Secure Guest User Record Access setting value from Setup > Sharing Settings.
2. **Configure Search Manager scope**: In Experience Builder > Search, add only the objects that should appear in results. Verify each object has "Allow Search" enabled in Setup > Object Manager and has at least one searchable field. Remove objects that should not be exposed to site visitors.
3. **Place the correct search component**: For LWR sites, place the `Search Bar` component in the header region and the `Search Results` component on the search results page. For Aura sites, use the `Search` component. Do not mix components across template types.
4. **Configure guest user access if required**: Enable the Guest User profile's object-level read permission for each searchable object. Create sharing rules or set OWDs to make relevant records accessible to guests. Validate under the Secure Guest User Record Access setting's current state.
5. **Set up federated search if required**: Register the external endpoint in Setup > Federated Search, validate the endpoint responds within the timeout, enable it in Search Manager, and test with a cross-system query. Build a custom `federatedSearchResult` LWC if a non-default result layout is needed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Site template type confirmed (LWR or Aura) and only the matching standard search component is placed
- [ ] Search Manager scope contains only the objects the site should expose
- [ ] All objects in scope have "Allow Search" enabled and at least one indexed field
- [ ] Guest user scenarios: Secure Guest User Record Access setting reviewed; sharing rules or OWDs configured for each object
- [ ] Federated search endpoint tested end-to-end from a site visitor session (not an admin preview)
- [ ] Search tested as a real guest user (incognito/unauthenticated) — admin Experience Builder preview bypasses guest sharing

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **LWR and Aura search components are not interchangeable** — The Aura `Search` component does not render on LWR pages; the LWR `Search Bar`/`Search Results` components are not available in Aura sites. Dropping the wrong component type produces no error in Experience Builder but results in a broken or empty search experience at runtime.
2. **Secure Guest User Record Access silently removes search results** — When this org setting is enabled (the Salesforce-enforced default going forward), guest users see only records they own or that are explicitly shared with the Guest User via sharing rules. A guest search against an object with OWD set to Public Read Only still returns zero results if no sharing rule exists, because the setting overrides the OWD for guests. No error is thrown.
3. **Object missing from Search Manager does not produce an error** — If a searchable object is absent from the site's Search Manager scope, search queries simply never return results for that object. There is no warning in the UI or in the search response. This is easily confused with a permissions or indexing problem.
4. **Federated search requires the external endpoint to handle the callout** — Salesforce's search infrastructure makes the outbound HTTP request to the external endpoint. There is no Apex @future or Queueable involved. If the endpoint is behind a firewall, IP allowlisting for Salesforce's outbound IP ranges is required. A timeout or non-200 response from the external endpoint silently suppresses the external results without surfacing an error to the end user.
5. **Admin Experience Builder preview does not replicate guest sharing** — Testing search as an administrator in Experience Builder preview bypasses all sharing restrictions. Records that appear in the admin preview may be invisible to actual guest users. Always validate guest search behavior in an incognito browser session against the live or preview site URL.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Search Manager configuration | Per-site object scope, promoted terms, and filter fields configured in Experience Builder |
| Guest user sharing checklist | Documented OWD values, sharing rules, and Secure Guest User Record Access setting state for each searchable object |
| Federated search endpoint spec | External endpoint URL, authentication configuration, and result schema mapping registered in Setup |
| Custom `federatedSearchResult` LWC | (Optional) Custom result card component for non-default federated result layouts |
| Custom search LWC using `lightning/uiSearchApi` | (Optional) Fully custom search UI for LWR sites that need non-standard result rendering |

---

## Related Skills

- `lwc/knowledge-article-lwc` — Building LWC components that retrieve and display Knowledge articles; covers data category visibility required for Knowledge to appear in search
- `lwc/experience-cloud-lwc-components` — General LWC component development for Experience Cloud pages
- `architect/knowledge-vs-external-cms` — Architecture tradeoffs between Salesforce Knowledge, CMS Connect, and federated external content for search strategies
- `architect/case-deflection-strategy` — Portal search as a case deflection mechanism; covers Knowledge-led self-service with federated search patterns
