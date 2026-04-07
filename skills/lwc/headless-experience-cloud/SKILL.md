---
name: headless-experience-cloud
description: "Use when building custom frontends (React, Vue, mobile, static sites) that consume Salesforce CMS content via the Connect REST API headless delivery endpoint. Triggers: 'headless Salesforce CMS', 'deliver CMS content to external frontend', 'React app Salesforce content API', 'custom frontend Experience Cloud data', 'CMS delivery channel API'. NOT for standard Experience Builder site development. NOT for CMS Connect (3rd-party CMS federation into Experience Builder). NOT for Experience Cloud LWC components rendered inside a site."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
triggers:
  - "headless Salesforce CMS — building a custom frontend that pulls content from a Salesforce org"
  - "deliver CMS content to external frontend — React, Vue, mobile app, or static site consuming SF CMS"
  - "React app Salesforce content API — fetching news, banners, or rich content from an org via REST"
  - "custom frontend Experience Cloud data — non-Experience Builder frontend needing CMS articles or media"
  - "CMS delivery channel — obtaining or using a channel ID to gate headless content access"
tags:
  - headless-cms
  - experience-cloud
  - connect-rest-api
  - cms-delivery
  - external-frontend
inputs:
  - Channel ID for the target CMS delivery channel (public or authenticated)
  - Content type names to filter (e.g., news, banner, sfdc_cms__news)
  - Auth strategy — public channel (no auth) vs authenticated channel (OAuth connected app)
  - CORS origin of the external frontend
outputs:
  - Guidance on constructing the Connect REST API content delivery request
  - Decision on public vs authenticated channel setup
  - CORS configuration steps for cross-origin access
  - Pagination strategy for large content collections
  - Code sketch for a React or mobile client consuming the endpoint
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Headless Experience Cloud

Use this skill when a custom frontend — React app, Vue SPA, mobile app, or static site — needs to consume Salesforce CMS content via the Connect REST API headless delivery endpoint. It covers channel setup, public vs authenticated access, CORS, pagination, and content-type filtering, and explicitly excludes standard Experience Builder development and CMS Connect federation.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Channel ID** — the headless delivery endpoint is gated by a channel ID. The ID is not displayed in the Experience Cloud site setup UI by default; retrieve it via Workbench or the Connect REST API (`GET /connect/cms/delivery/channels`).
- **Channel type** — public channels allow unauthenticated requests; authenticated channels require an OAuth 2.0 connected app with the `chatter_api` or `api` scope. Confirm which type the org has configured.
- **CORS policy** — cross-origin requests from an external frontend domain must be explicitly allowed in Setup > CORS. Missing this is the most common first-day blocker.
- **Feature distinction** — CMS Connect (federating a 3rd-party CMS like Contentful into Experience Builder pages) is a completely different feature from the headless delivery API (pushing SF CMS content out to external systems). Confirm which capability the stakeholder actually needs before proceeding.

---

## Core Concepts

### The Connect REST API CMS Delivery Endpoint

Salesforce CMS exposes content to external consumers through a single Connect REST API resource family:

```
GET /services/data/v{api-version}/connect/cms/delivery/channels/{channelId}/contents
```

Key behaviors:
- `{channelId}` is the unique identifier for a CMS delivery channel (not a site ID or community ID).
- The response returns a paginated list of content items matching the channel's published content.
- Filter by content type using the `contentTypeName` query parameter (e.g., `contentTypeName=sfdc_cms__news`).
- Retrieve a single content item: `GET /connect/cms/delivery/channels/{channelId}/contents/{contentKey}`.
- The API version must be API v49.0 (Summer '20) or later; v58.0+ is recommended for current features.

### Public vs Authenticated Channels

Salesforce CMS delivery channels come in two access modes:

| Mode | Auth Required | Use Case |
|---|---|---|
| Public channel | None — anonymous GET requests succeed | Marketing sites, public portals, static site generators |
| Authenticated channel | OAuth 2.0 Bearer token | Member portals, personalized content, gated content |

For authenticated channels, the calling application must obtain an access token via a connected app using the OAuth 2.0 client credentials or web server flow. The connected app needs the `api` or `chatter_api` OAuth scope. The token is passed as `Authorization: Bearer {token}` in each request.

Even on public channels, Salesforce org IP allowlisting and CORS policies still apply for browser-based clients.

### CMS Connect vs Headless Delivery API — Critical Distinction

These two features share the word "CMS" and both involve Experience Cloud, but they are completely different:

| Feature | Direction | Purpose |
|---|---|---|
| **Headless delivery API** | SF CMS → external frontend | Push Salesforce-authored content to React/mobile/static clients |
| **CMS Connect** | 3rd-party CMS → Experience Builder | Pull external CMS content (WordPress, Contentful) into an Experience Builder page component |

Confusing the two leads to looking in completely the wrong part of Setup and the documentation. If the requirement is "show Salesforce-authored content in a React app", that is the headless delivery API. If the requirement is "show WordPress content in an Experience Builder page", that is CMS Connect.

### CORS Setup for Browser Clients

Any frontend running in a browser that calls the delivery endpoint from a different origin than the Salesforce org must be listed in Setup > Security > CORS Allowed Origins List. Without this, the browser blocks the preflight `OPTIONS` request and the fetch fails with a CORS error before any Salesforce response is received.

Steps:
1. Setup > Security > CORS.
2. Add the external frontend origin (e.g., `https://www.mysite.com`).
3. Wildcards are not allowed — list each origin explicitly.
4. For local development, add `http://localhost:3000` (or whatever port the dev server uses) as a separate entry.

---

## Common Patterns

### Pattern 1: Public CMS Channel — React App Fetching Content

**When to use:** The content is publicly accessible (no login required) and the frontend is a React or static-site app hosted outside Salesforce.

**How it works:**

1. Retrieve the channel ID using Workbench: `GET /services/data/v62.0/connect/cms/delivery/channels` — find the channel whose `channelType` is `public` and copy its `id`.
2. Add the frontend's origin to the CORS allowed list in Setup.
3. In the React app, fetch content using the standard Fetch API:

```javascript
const CHANNEL_ID = 'YOUR_CHANNEL_ID';
const SF_INSTANCE = 'https://yourorg.my.salesforce.com';
const API_VERSION = 'v62.0';

async function fetchNewsContent(pageSize = 10, pageParam = 1) {
  const url = new URL(
    `${SF_INSTANCE}/services/data/${API_VERSION}/connect/cms/delivery/channels/${CHANNEL_ID}/contents`
  );
  url.searchParams.set('contentTypeName', 'sfdc_cms__news');
  url.searchParams.set('pageSize', String(pageSize));
  url.searchParams.set('page', String(pageParam));

  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(`CMS fetch failed: ${response.status}`);
  return response.json();
}
```

4. The response includes a `currentPageUrl`, `nextPageUrl`, and `items` array. Use `nextPageUrl` to paginate.

**Why not the alternative:** Using the Experience Cloud Guest User Apex endpoint or a custom Apex REST resource adds unnecessary complexity and bypasses the purpose-built delivery API.

### Pattern 2: Authenticated Channel — Mobile App with OAuth

**When to use:** Content is gated to authenticated users (member portal, personalized banners) and the consumer is a mobile app or server-side renderer.

**How it works:**

1. Create a Connected App in Setup with OAuth scopes `api` and `refresh_token`.
2. Use the OAuth 2.0 client credentials flow (server-to-server) or web server flow (user-facing) to obtain an access token.
3. Pass the token in every delivery API request:

```javascript
async function fetchAuthenticatedContent(accessToken, channelId, contentType) {
  const SF_INSTANCE = 'https://yourorg.my.salesforce.com';
  const API_VERSION = 'v62.0';
  const url = `${SF_INSTANCE}/services/data/${API_VERSION}/connect/cms/delivery/channels/${channelId}/contents?contentTypeName=${contentType}`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) throw new Error(`Authenticated CMS fetch failed: ${response.status}`);
  return response.json();
}
```

4. Implement token refresh using the `refresh_token` grant before the access token expires (default: 2 hours).

**Why not the alternative:** Embedding long-lived session IDs in a mobile app is a security risk. OAuth connected app tokens are scoped, rotatable, and auditable.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| External React app, public marketing content | Public channel + CORS | No auth overhead; simplest path for anonymous content |
| Member portal with personalized content | Authenticated channel + OAuth web server flow | Tokens are user-scoped; content visibility can differ per user |
| Server-side renderer or build-time static generation | Authenticated channel + client credentials flow | No user present; service-to-service token is appropriate |
| Content from WordPress/Contentful in Experience Builder | CMS Connect (separate feature) | Headless delivery API is for SF CMS content going out, not 3rd-party CMS coming in |
| LWC component inside an Experience Builder page | Standard Experience Builder development | Headless API is not needed; the LWC runs inside the platform |
| Large content library, need to page results | Paginated delivery API with `nextPageUrl` | Built-in pagination; avoid fetching all items in one call |

---

## Recommended Workflow

Step-by-step instructions for building a headless Experience Cloud integration:

1. **Confirm the requirement** — verify the frontend is external to Salesforce (not an LWC in Experience Builder) and the content source is Salesforce CMS (not a 3rd-party CMS via CMS Connect). These two checks prevent building the wrong thing.
2. **Retrieve the channel ID** — use Workbench (`GET /services/data/v62.0/connect/cms/delivery/channels`) or the Setup UI (rarely shows the raw ID) to get the exact channel ID. Confirm whether the channel type is `public` or `authenticated`.
3. **Configure CORS and auth** — for browser clients, add the frontend origin to Setup > Security > CORS. For authenticated channels, create or identify a Connected App and confirm the OAuth scopes (`api` or `chatter_api`).
4. **Build the fetch layer** — implement the delivery API call with content type filtering (`contentTypeName`) and pagination (`page`, `pageSize`). Handle `nextPageUrl` from the response for multi-page content.
5. **Test across environments** — channel IDs differ between production, sandboxes, and scratch orgs. Externalize the channel ID as an environment variable and verify the correct ID is used in each environment before go-live.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Channel ID confirmed via API or Workbench — not assumed from the UI
- [ ] Channel type (public vs authenticated) matches the access strategy implemented
- [ ] CORS allowed origin added for every external frontend domain (including localhost for dev)
- [ ] Connected App configured with correct OAuth scopes if using an authenticated channel
- [ ] Content type name (`contentTypeName`) matches a type published on the channel
- [ ] Pagination implemented using `nextPageUrl` — not a hard-coded page count
- [ ] Channel ID externalized as an environment variable — not hardcoded in application code
- [ ] CMS Connect not confused with headless delivery API (confirmed in requirements)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Channel ID is not in the Setup UI** — The CMS delivery channel ID is a 18-character record ID that is not displayed in the Experience Workspaces or CMS Home UI. Practitioners must retrieve it via `GET /connect/cms/delivery/channels` using Workbench, Postman, or the CLI. Hardcoding a wrong ID produces a 404 with no helpful error message.
2. **CMS Connect and headless delivery are named similarly but are opposite features** — CMS Connect federates external CMS content INTO Experience Builder. The headless delivery API sends SF CMS content OUT to external frontends. These are configured in completely different places in Setup, and the documentation lives in separate sections of the developer guide.
3. **Public channel requests can still be blocked by IP restrictions** — A public channel requires no authentication, but the Salesforce org may have network-level IP restrictions (Trusted IP Ranges in Setup) that block requests from external server IPs. This typically surfaces in CI pipelines or server-side renderers running from cloud IP ranges not in the trusted list.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Delivery API fetch function | JavaScript/TypeScript function targeting the correct channel endpoint with auth headers and pagination |
| Connected App configuration | OAuth scopes and callback URL setup for authenticated channel access |
| CORS origin entries | List of frontend origins to add to Setup > Security > CORS |
| Environment variable manifest | Channel ID and instance URL externalized per environment |

---

## Related Skills

- architect/knowledge-vs-external-cms — when to use Salesforce Knowledge vs an external CMS vs Salesforce CMS; use alongside this skill when the content architecture decision is still open
