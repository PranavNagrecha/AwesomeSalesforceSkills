---
name: service-cloud-rest-api
description: "Use this skill when integrating with Salesforce Service Cloud REST APIs — specifically the Knowledge REST API (/knowledgeManagement/ for authoring, /support/knowledgeWithSEO/ for guest retrieval) and the Messaging for In-App and Web (MIAW) Enhanced Chat API. Trigger keywords: Knowledge article retrieval, data category filtering, URL-name lookup, Enhanced Chat API, legacy Chat REST API migration. NOT for generic REST API callouts from Apex (use apex__http-callouts), NOT for Salesforce REST API CRUD on standard objects, NOT for Einstein Bot configuration."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I retrieve Knowledge articles via REST API filtered by data category?"
  - "We need to migrate from the legacy Salesforce Chat REST API — what replaces it?"
  - "How do I look up a Knowledge article by its URL name using the Salesforce REST API?"
  - "What is the correct endpoint to serve Knowledge articles to unauthenticated guest users?"
  - "How does the Enhanced Chat API (MIAW) differ from the old Chat REST API?"
tags:
  - service-cloud
  - knowledge
  - rest-api
  - chat-api
  - miaw
  - enhanced-chat
  - legacy-chat-migration
  - data-categories
inputs:
  - "Salesforce org API version (must be v44+ for URL-name Knowledge lookup)"
  - "Authentication context: authenticated agent/internal user vs. unauthenticated guest/Experience Cloud visitor"
  - "Knowledge article data category group and category values in scope"
  - "Whether the org uses legacy Chat REST API or is targeting Enhanced Chat API (MIAW)"
outputs:
  - "Correct REST endpoint patterns for Knowledge authoring, retrieval, and guest SEO access"
  - "Migration decision guidance from legacy Chat REST API to Enhanced Chat API (MIAW)"
  - "Data category filter query construction for Knowledge article retrieval"
  - "URL-name-based article lookup pattern (API v44+)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Service Cloud REST API

This skill activates when a practitioner needs to call Salesforce Service Cloud REST APIs — either the Knowledge REST API (both the internal authoring surface and the guest-facing SEO retrieval surface) or the Messaging for In-App and Web (MIAW) Enhanced Chat API. It covers endpoint selection, authentication differences, data category filtering, legacy Chat REST API migration, and common integration patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- **API version:** The URL-name lookup for Knowledge articles requires API version 44.0 or later. Confirm the org's minimum API version before building integrations.
- **Authentication context:** The `/knowledgeManagement/` endpoint family requires an authenticated session (internal users, agents, or Apex callouts with a session ID). The `/support/knowledgeWithSEO/` endpoint family supports unauthenticated guest access — used for Experience Cloud portals and self-service sites. Using the wrong endpoint for the wrong context causes 401 errors or missing article results.
- **Chat API version in use:** Determine whether the org still uses the legacy Chat REST API (force.com/chat/rest/) or has migrated to Enhanced Chat API (Messaging for In-App and Web, MIAW). The legacy Chat REST API was retired on February 14, 2026. Any org still calling legacy Chat REST endpoints after that date receives failures.
- **Data category structure:** Knowledge article retrieval via data category filter requires knowing the data category group developer name and the category developer name. These must be URL-encoded in query parameters.
- **Knowledge article type metadata:** The v1 Knowledge REST API uses article type-specific endpoints. The v2 (unified) Knowledge REST API treats all articles uniformly under a single `knowledge__kav` object type.

---

## Core Concepts

### Knowledge REST API — Two Distinct Endpoint Families

Salesforce exposes two separate REST API families for Knowledge, each with a different authentication model and purpose:

**Internal/Authoring (`/knowledgeManagement/`):**
- Base path: `/services/data/vXX.X/knowledgeManagement/`
- Requires a valid authenticated Salesforce session (OAuth access token or Apex session ID)
- Used for: drafting, publishing, translating, managing article lifecycle, retrieving article content for agents
- Key resources: `/articles`, `/articles/{articleId}`, `/articleTypes`, `/articleTypes/{articleTypeName}/suggestedArticles`
- Returns full article field content including internal-only fields

**Guest/SEO Retrieval (`/support/knowledgeWithSEO/`):**
- Base path: `/services/data/vXX.X/support/knowledgeWithSEO/`
- Supports unauthenticated access when used with an Experience Cloud site that has guest user access enabled
- Used for: self-service portals, public knowledge bases, Experience Cloud deflection pages
- Returns articles filtered to those published and accessible to the guest user profile
- URL-name-based lookup available from API v44+: `/support/knowledgeWithSEO/articles?urlName=my-article-url-name`

Mixing up these two families is the most common integration error: an Apex callout using `/knowledgeManagement/` will fail in an Aura/LWC guest context; a portal site using `/support/knowledgeWithSEO/` will not return unpublished drafts.

### Data Category Filtering

Knowledge articles are organized into data categories (hierarchical classification trees). The REST API supports filtering by data category using query parameters:

- `categoryGroup` — developer name of the data category group (e.g., `Products`)
- `category` — developer name of the specific category (e.g., `Laptops`)
- `navigationType` — `standard` (default) or `classifyingArticles` — controls whether parent/child categories are included

Example query string: `?categoryGroup=Products&category=Laptops`

Data category names are case-sensitive and must match the developer name exactly, not the label. A mismatch returns an empty result set with no error, which is a common silent failure mode.

Visibility of articles by data category is also governed by the user's data category visibility settings. An authenticated user who lacks visibility to a category will receive an empty result even if articles exist — there is no permission error thrown.

### Legacy Chat REST API vs. Enhanced Chat API (MIAW)

Salesforce had two separate live-chat REST API surfaces:

**Legacy Chat REST API (retired February 14, 2026):**
- Base path: `https://<instance>.salesforce.com/chat/rest/`
- Used the `X-LIVEAGENT-API-VERSION` header and `X-LIVEAGENT-SESSION-KEY` header pair
- Required a separate chat endpoint hostname distinct from the Salesforce instance URL
- Session lifecycle: `/System/SessionId` → `/Chasitor/ChasitorInit` → polling `/System/Messages`

**Enhanced Chat API — Messaging for In-App and Web (MIAW):**
- Part of the Salesforce Omni-Channel Messaging platform
- Uses standard OAuth 2.0 bearer tokens — no custom headers required
- Conversation lifecycle managed via Salesforce Platform Event streaming and REST resources under `/services/data/vXX.X/connect/messaging/`
- Supports persistent conversation history, async messaging, and rich media — capabilities not available in legacy Chat REST API
- Agent-facing events flow through Omni-Channel rather than a long-poll loop

After February 14, 2026, any integration still targeting legacy Chat REST endpoints (`/chat/rest/`) receives HTTP errors. Migrating requires replacing the entire client session lifecycle — there is no backward-compatible wrapper.

---

## Common Patterns

### Pattern 1: Knowledge Article Retrieval with Data Category Filter (Authenticated)

**When to use:** An Apex class, Visualforce page, or LWC (in authenticated context) needs to programmatically fetch Knowledge articles filtered to a specific product line or topic.

**How it works:**

1. Obtain an OAuth access token or use the current session ID in Apex (`UserInfo.getSessionId()`).
2. Construct the request to `/services/data/v62.0/knowledgeManagement/articles` with query params.
3. Pass `categoryGroup` and `category` as query parameters.
4. Deserialize the JSON response into Apex wrapper classes.

Key request shape:
```
GET /services/data/v62.0/knowledgeManagement/articles?categoryGroup=Products&category=Laptops&pageSize=10
Authorization: Bearer <access_token>
```

Response contains `articles` array with `id`, `title`, `summary`, `urlName`, `articleType`, `publishStatus`, `lastPublishedDate`.

**Why not SOQL directly:** SOQL on `Knowledge__kav` does not respect data category visibility for guests, and does not produce SEO-friendly URL name lookups. REST API respects the full sharing and visibility stack.

### Pattern 2: Guest-Facing Article Lookup by URL Name (Experience Cloud)

**When to use:** An Experience Cloud self-service site needs to render a full Knowledge article using its URL slug (e.g., `/help/how-to-reset-password`), without requiring the visitor to log in.

**How it works:**

1. Enable Knowledge for the Experience Cloud site and set the guest user profile's data category visibility.
2. Make an unauthenticated REST call (or via Connected App with the site's guest user context) to:
   ```
   GET /services/data/v62.0/support/knowledgeWithSEO/articles?urlName=how-to-reset-password
   ```
3. The response returns the full article body, metadata, and related categories for the matching URL name.
4. If the URL name does not match any article visible to the guest profile, the response returns an empty `articles` array (not a 404).

**Why not the authoring endpoint:** `/knowledgeManagement/` requires authentication and returns draft articles — unsuitable for public-facing rendering.

### Pattern 3: Migrating Legacy Chat REST API to Enhanced Chat API (MIAW)

**When to use:** Any org that has live code or integrations using the legacy Chat REST API (`/chat/rest/`) that must be migrated before or after the February 14, 2026 retirement deadline.

**How it works:**

1. Audit all integration points calling `<instance>.salesforce.com/chat/rest/` — check Apex `HttpRequest` callouts, external middleware, and mobile SDKs.
2. Provision an Enhanced Messaging Channel in Setup > Messaging Settings. Select "In-App and Web" channel type.
3. Replace `X-LIVEAGENT-*` header-based session initiation with an OAuth 2.0 Connected App flow.
4. Replace the long-poll `GET /System/Messages` loop with Platform Event subscription to `ConversationIntelligenceEvent__e` or use the MIAW SDK for web/mobile.
5. Map legacy transcript objects (`LiveChatTranscript`) to their MIAW equivalents (`MessagingSession`).

**Why not keep legacy Chat REST:** The endpoint is retired and returns errors post-February 14, 2026. There is no official compatibility shim.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Authenticated agent needs article list filtered by data category | `GET /knowledgeManagement/articles?categoryGroup=X&category=Y` | Authoring endpoint respects agent sharing model |
| Unauthenticated guest needs to render article by URL slug | `GET /support/knowledgeWithSEO/articles?urlName=<slug>` | Guest-friendly endpoint, supports URL-name lookup (v44+) |
| Org uses legacy Chat REST API (post-Feb 2026) | Migrate to MIAW Enhanced Chat API | Legacy Chat REST API retired Feb 14, 2026 |
| Need to check if a category group/category name is correct | Query data category visibility in Setup and use developer names | Labels ≠ developer names; mismatch silently returns empty results |
| LWC in Experience Cloud needs to fetch articles without exposing credentials | Use `getRecord` Lightning Data Service or Apex `@AuraEnabled` with `without sharing` scoped to Knowledge | Avoids exposing OAuth tokens in client-side JavaScript |
| Need article content for AI summarization in Apex | Use `/knowledgeManagement/articles/{id}` with `Accept: application/json` | Returns full article body fields unlike SOQL which truncates rich text |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify authentication context** — Determine whether the integration will run as an authenticated internal user/agent or as an unauthenticated guest. This determines which endpoint family (`/knowledgeManagement/` vs. `/support/knowledgeWithSEO/`) to use and whether a Connected App with OAuth is needed.
2. **Confirm API version** — Verify the org's minimum API version. URL-name lookup requires v44+. Use the highest available API version (e.g., v62.0 for Spring '25) to access the latest resource shapes.
3. **Check data category configuration** — For any category-filtered retrieval, confirm the data category group and category developer names in Setup > Data Categories. Verify the user or guest profile has the correct data category visibility assignments.
4. **Audit legacy Chat REST usage** — Run a codebase search for `/chat/rest/` and `X-LIVEAGENT-API-VERSION`. Any hit requires MIAW migration. Document each call site with its session lifecycle step.
5. **Construct and test REST calls** — Build the endpoint URL, add required headers (`Authorization: Bearer`, `Content-Type: application/json`), and validate the response shape in Workbench or Postman before implementing in Apex.
6. **Implement Apex callout with proper error handling** — Wrap `Http.send()` in try/catch, check `HttpResponse.getStatusCode()` for 200/201 vs. 4xx/5xx, parse the JSON body, and handle the empty-array case for data category mismatches.
7. **Validate with a Review Checklist pass** — Confirm no legacy Chat REST references remain, no hardcoded category names, correct endpoint family for the auth context, and that test coverage includes the empty-result case.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Correct endpoint family used for authentication context (`/knowledgeManagement/` for authenticated, `/support/knowledgeWithSEO/` for guest)
- [ ] API version is v44+ if URL-name lookup is used
- [ ] Data category developer names (not labels) used in query parameters
- [ ] No remaining references to legacy Chat REST API (`/chat/rest/` or `X-LIVEAGENT-*` headers)
- [ ] Empty-array response handled explicitly (not treated as an error, but not silently ignored)
- [ ] OAuth access token or session ID is not exposed in client-side JavaScript
- [ ] Apex test class mocks the `HttpResponse` for both success and empty-result scenarios

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Data category mismatch returns empty array, not an error** — If the `categoryGroup` or `category` parameter value does not match an existing developer name (including case), the API returns `{"articles": [], "total": 0}` with HTTP 200. There is no error message. This silently breaks filtering and is indistinguishable from "no articles exist" without inspecting Setup.
2. **Legacy Chat REST API is retired** — Any callout to `<instance>.salesforce.com/chat/rest/` after February 14, 2026 returns an error. There is no deprecation grace period or backward-compatible redirect. Orgs that missed the migration deadline must treat this as an emergency remediation.
3. **`/knowledgeManagement/` returns drafts; `/support/knowledgeWithSEO/` does not** — The authoring endpoint includes draft and archived articles in results when the `publishStatus` filter is omitted. A portal that accidentally uses the authoring endpoint (with an admin session) may display unpublished articles to visitors.
4. **Guest user data category visibility must be explicitly configured** — Even if articles are published, an Experience Cloud guest user will receive an empty result from `/support/knowledgeWithSEO/` unless the guest user profile has been granted data category visibility in Setup > Data Category Visibility. This is a separate setting from the article's publication status.
5. **URL-name uniqueness is not enforced across article types** — If two articles of different types share the same `urlName`, the `/support/knowledgeWithSEO/articles?urlName=<slug>` endpoint may return multiple results or only the first match depending on API version. Use article-type-specific filtering when URL names are not guaranteed unique.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Endpoint selection decision | Documented choice of `/knowledgeManagement/` vs. `/support/knowledgeWithSEO/` with justification |
| Apex callout class | `HttpRequest`/`HttpResponse` wrapper with JSON deserialization and empty-result handling |
| Data category parameter map | Validated developer names for `categoryGroup` and `category` query parameters |
| MIAW migration checklist | List of legacy Chat REST call sites replaced with Enhanced Chat API equivalents |

---

## Related Skills

- `architect/service-cloud-architecture` — Service Cloud solution architecture including Knowledge as a deflection engine and channel strategy
- `agentforce/einstein-copilot-for-service` — Einstein Article Recommendations and Service Replies that consume Knowledge articles internally
