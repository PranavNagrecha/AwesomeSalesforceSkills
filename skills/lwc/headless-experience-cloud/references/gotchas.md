# Gotchas — Headless Experience Cloud

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CMS Connect and the Headless Delivery API Are Completely Different Features

**What happens:** A practitioner searching for "headless CMS Salesforce" finds CMS Connect documentation first, configures a CMS Connect source pointing at an external CMS, and wonders why there is no API to deliver Salesforce-authored content to their React app. Alternatively, they find the headless delivery API and try to use it to pull WordPress content into an Experience Builder page — also the wrong feature.

**When it occurs:** Any time the requirement involves either "push SF CMS content to an external frontend" or "pull external CMS into Experience Builder." The features share the name "CMS" and both appear under Experience Cloud in the documentation, making them easy to conflate.

**How to avoid:** Establish the direction first:
- Content going **out** of Salesforce to an external system → headless delivery API (`/connect/cms/delivery/channels/{channelId}/contents`).
- Content coming **in** from a 3rd-party CMS into an Experience Builder page → CMS Connect (a separate setup under CMS in the Experience Workspaces UI).

Document this distinction in the requirements phase before touching any configuration.

---

## Gotcha 2: Channel ID Is Not Visible in the Standard UI — Must Be Retrieved via API

**What happens:** The practitioner opens Experience Workspaces or CMS Home in Setup and cannot find anything labeled "channel ID." They search the org and cannot locate a field showing the 18-character ID. They either guess (and use the wrong ID) or give up and assume the feature is not enabled.

**When it occurs:** Any time a developer needs to construct the delivery API URL. The channel ID is a core required path parameter — without the exact value, every request returns 404.

**How to avoid:** Retrieve the channel ID via the API before starting development:
```
GET /services/data/v62.0/connect/cms/delivery/channels
```
Use Workbench (workbench.developerforce.com), the Salesforce CLI (`sf apex run`), or Postman. The response includes `channelId` for each configured channel. Record the value in the project's environment variable documentation immediately so it does not need to be retrieved again during incidents.

---

## Gotcha 3: Public Channel Requests Can Still Be Blocked by IP Restrictions

**What happens:** The team configures a public channel and omits any OAuth setup, expecting anonymous requests to just work. Requests from CI/CD pipelines, static-site generators running on cloud build servers, or server-side renderers fail with a connection error or a 403. Local development works fine because the developer's office IP is on the trusted list.

**When it occurs:** When the Salesforce org has Trusted IP Ranges configured in Setup > Network Access. A "public" channel means no user authentication is required, but it does not bypass network-level IP restrictions. Cloud provider IP ranges (AWS, GCP, Azure, Vercel, Netlify, etc.) are rarely on an org's trusted list.

**How to avoid:** Check Setup > Network Access to see whether Trusted IP Ranges are configured. If they are, either:
- Add the external service's egress IP range to the trusted list (risky if the range is wide or changes).
- Switch to an authenticated channel and use a service account — the OAuth token flow is not subject to the same IP restrictions as anonymous requests.
- Use a proxy layer hosted within a trusted IP range to forward delivery API requests.

---

## Gotcha 4: CORS Errors Are Silent from the Salesforce Side

**What happens:** The React app makes a fetch to the delivery API endpoint, and the browser console shows a CORS error. The developer checks Salesforce debug logs expecting to see a CORS rejection, but there are no logs — because the preflight OPTIONS request is blocked before Salesforce ever processes it at the application layer.

**When it occurs:** Any browser-based frontend calling the delivery API from an origin not listed in Setup > Security > CORS. The error manifests as "Access to fetch at '...' from origin '...' has been blocked by CORS policy."

**How to avoid:** Add every origin that will call the endpoint — including `http://localhost:{port}` for local development — to Setup > Security > CORS before writing a single line of frontend code. Wildcards are not supported. After adding origins, allow a few minutes for the change to propagate before testing.

---

## Gotcha 5: Content Type Names Are Case-Sensitive and Org-Specific

**What happens:** The developer uses `contentTypeName=news` as a filter parameter, gets an empty `items` array back, and assumes the channel has no content. The channel has content, but the actual content type name in that org is `sfdc_cms__news` (for standard types) or a custom name like `My_Company__press_release`.

**When it occurs:** When filtering delivery API responses by content type. The `contentTypeName` query parameter must exactly match the API name of the content type as defined in the org's CMS setup.

**How to avoid:** Retrieve available content types for the channel first:
```
GET /services/data/v62.0/connect/cms/delivery/channels/{channelId}/content-types
```
This returns the exact `contentTypeName` values available on that channel. Use these values — do not guess based on display labels, which may differ from API names.
