# Headless Experience Cloud — Integration Design Template

Use this template when designing or implementing a Salesforce CMS headless delivery integration for a custom frontend.

---

## Scope

**Skill:** `headless-experience-cloud`

**Request summary:** (fill in what the user asked for)

**Frontend type:** [ ] React SPA  [ ] Vue SPA  [ ] Static site generator  [ ] Mobile app (iOS/Android/React Native)  [ ] Server-side renderer  [ ] Other: ___

---

## Context Gathered

Answer each question from SKILL.md `## Before Starting` before proceeding.

| Question | Answer |
|---|---|
| Channel ID (retrieved via API, not guessed) | |
| Channel type (public or authenticated) | |
| Frontend origin(s) requiring CORS entries | |
| Salesforce org instance URL | |
| API version to use | v62.0 (or confirm latest) |
| Content type names available on this channel | |

---

## Auth Strategy

**Channel type:** [ ] Public (no auth)  [ ] Authenticated (OAuth)

If authenticated:

| Item | Value |
|---|---|
| Connected App name | |
| OAuth flow (client credentials / web server) | |
| OAuth scopes (minimum: api or chatter_api) | |
| Access token expiry (default: 2 hours) | |
| Refresh token required? [ ] Yes  [ ] No | |

---

## CORS Configuration

List every origin that will call the delivery API from a browser:

| Origin | Environment |
|---|---|
| https://www.yoursite.com | Production |
| https://staging.yoursite.com | Staging |
| http://localhost:3000 | Local development |

Action: Add all of the above to Setup > Security > CORS before writing frontend code.

---

## Environment Variable Manifest

Channel IDs and org-specific values must be externalized. Do not hardcode them.

| Variable Name | Dev Value | Staging Value | Production Value |
|---|---|---|---|
| `CMS_CHANNEL_ID` | | | |
| `SF_INSTANCE_URL` | | | |
| `SF_API_VERSION` | v62.0 | v62.0 | v62.0 |
| `CMS_CLIENT_ID` (authenticated only) | | | |

---

## Content Types to Fetch

List the `contentTypeName` values this integration will use. Retrieve exact names from:
```
GET /services/data/{version}/connect/cms/delivery/channels/{channelId}/content-types
```

| Display Name | `contentTypeName` API Value | Filtered Fetch? |
|---|---|---|
| | | |
| | | |

---

## Pagination Strategy

**Default page size:** ___ (recommended: 10–25 for UI display, up to 250 for build-time generation)

**Pagination approach:**
- [ ] Single page (fixed count for homepage widgets or carousels)
- [ ] Infinite scroll / load more (follow `nextPageUrl` from response)
- [ ] Build-time full fetch (static site generator — collect all pages at build time)

---

## Pattern Selected

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Public CMS Channel — React App Fetching Content
- [ ] Pattern 2: Authenticated Channel — Mobile App with OAuth
- [ ] Custom pattern (describe): ___

**Reason for selection:**

---

## Checklist

Copy from SKILL.md `## Review Checklist` and tick items as you complete them:

- [ ] Channel ID confirmed via API or Workbench — not assumed from the UI
- [ ] Channel type (public vs authenticated) matches the access strategy implemented
- [ ] CORS allowed origin added for every external frontend domain (including localhost)
- [ ] Connected App configured with correct OAuth scopes (if authenticated channel)
- [ ] Content type name (`contentTypeName`) matches a type published on the channel
- [ ] Pagination implemented using `nextPageUrl` — not a hard-coded page count
- [ ] Channel ID externalized as an environment variable — not hardcoded in application code
- [ ] CMS Connect not confused with headless delivery API (confirmed in requirements)

---

## Notes

Record any deviations from the standard pattern and why:
