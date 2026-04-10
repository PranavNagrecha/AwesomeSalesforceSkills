---
name: marketing-cloud-custom-activities
description: "Use when building, debugging, or architecting a custom activity, custom split activity, or custom entry source for Marketing Cloud Journey Builder. Trigger keywords: custom activity, Postmonger, config.json, Journey Builder execute endpoint, customActivity.js, custom split outcome, installed package app extension, Journey Builder REST API. NOT for standard Journey Builder canvas configuration, out-of-the-box activity settings, Email Studio send activities, or general Marketing Cloud automation."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "how do I build a custom activity for Journey Builder using config.json and Postmonger"
  - "Journey Builder custom activity execute endpoint not responding or contacts erroring out"
  - "Postmonger requestedSchema never fires and field mapping is blank in my custom activity UI"
  - "custom split activity not routing contacts to correct branch outcome"
  - "Journey Builder custom entry source not triggering contacts into journey"
  - "JWT verification for Marketing Cloud Journey Builder execute endpoint"
  - "custom activity iframe not loading in Journey Builder canvas"
tags:
  - marketing-cloud
  - journey-builder
  - custom-activity
  - postmonger
  - installed-package
  - rest-api
  - integration
inputs:
  - "Marketing Cloud business unit and Installed Package credentials (client ID, client secret)"
  - "Publicly hosted HTTPS endpoint(s) for the activity UI web app and execute/save/publish/validate callbacks"
  - "Activity schema: what data from the contact record or journey context the activity needs"
  - "For custom splits: list of outcome branches with keys and display labels"
  - "JWT validation strategy for securing the execute endpoint"
outputs:
  - "config.json defining the application extension for the Installed Package"
  - "customActivity.js implementing Postmonger event handlers"
  - "Hosted web app HTML/JS serving the activity configuration UI"
  - "Server-side execute endpoint implementation returning HTTP 200 with outcome key"
  - "Review checklist confirming HTTPS, JWT verification, and timeout handling"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Marketing Cloud Custom Activities

This skill activates when a practitioner needs to build or troubleshoot a custom activity, custom split activity, or custom entry source for Marketing Cloud Journey Builder using the three-part framework: config.json (application extension definition), customActivity.js (Postmonger-based UI messaging), and a publicly hosted HTTPS web application with REST callback endpoints.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Installed Package access:** Confirm the Marketing Cloud account has an Installed Package (Setup > Apps > Installed Packages) with an App Extension of type "Journey Builder Activity" already created or ready to create. The package provides the client ID and secret needed for API auth.
- **Hosting infrastructure:** The custom activity UI and callback endpoints must be served over HTTPS from a publicly reachable host. Journey Builder will refuse to load an HTTP-only iframe. Confirm the hosting environment (Heroku, AWS, Azure, etc.) and that TLS is provisioned.
- **Common wrong assumption:** Practitioners often assume the execute endpoint can return custom JSON payloads with a 200 status. Journey Builder only checks for HTTP 200 to advance the contact; any non-200 response causes the contact to error out of the journey regardless of the response body.
- **Limits and constraints:** The execute endpoint must respond within the configured timeout window (default 30 seconds; configurable per activity). Long-running operations must be made asynchronous — accept the request, enqueue the real work, and return 200 immediately. Journey Builder does not retry on timeout; the contact errors out.

---

## Core Concepts

### 1. Three-Part Framework

A custom Journey Builder activity has three required components that must work together:

**config.json** is the application extension definition registered in the Installed Package. It declares the activity's endpoints (execute, save, publish, validate), the configurable arguments schema (what data the journey canvas passes to the activity), metaData including the activity icon, and for custom splits, the `outcomes` array defining each branch key and label. Journey Builder reads this file at design time to render the activity on the canvas and at runtime to invoke the correct endpoint.

**customActivity.js** runs in the activity's configuration iframe inside Journey Builder. It uses the Postmonger library — a cross-frame messaging adapter — to communicate with the Journey Builder host application. The script must listen for the `ready` event before calling any `trigger:` methods. Key events include `requestedSchema` (returns the journey entry event schema), `requestedData` (returns current activity arguments), `requestedInteractionDefaults` (returns journey-level defaults), and `updatedActivity` (fired when the practitioner saves activity configuration in the canvas).

**Hosted web app** is the HTML/JavaScript application served over HTTPS that Journey Builder loads in an iframe when a practitioner opens the activity's configuration panel. It hosts customActivity.js and any UI components for configuring the activity arguments. This app also exposes the REST callback endpoints (execute, save, publish, validate) that Journey Builder calls at runtime and during journey activation.

### 2. Execute Endpoint and JWT Security

When a journey contact reaches a custom activity step, Journey Builder POSTs to the configured execute URL. The POST body contains the contact's data (from the entry event schema) and journey context metadata. The request header includes a JWT (JSON Web Token) signed with the Installed Package secret. The receiving endpoint **must** verify this JWT before processing the request — failure to do so allows any caller to trigger the endpoint. After verification and processing, the endpoint must return HTTP 200 within the timeout. For custom splits, the 200 response body must contain a JSON object with a `branchResult` key matching one of the outcome keys defined in config.json.

### 3. Custom Splits and Outcome Keys

A custom split activity routes contacts to different journey branches based on logic in the execute endpoint. Outcomes are declared in config.json under `metaData.outcomes` as an array of objects, each with a `key` (the identifier the execute endpoint returns in `branchResult`) and a `label` (the display name shown on the Journey Builder canvas branch connector). The execute endpoint determines which branch to use and returns the appropriate key. If the returned key does not match any declared outcome, the contact errors out.

### 4. Postmonger Event Sequence

The Postmonger library enforces a strict initialization sequence. The customActivity.js must:
1. Instantiate the Postmonger session: `var connection = new Postmonger.Session()`
2. Register listeners for Journey Builder events before calling any trigger methods
3. Listen for `'ready'` — only after this event fires is the session initialized and safe to call `connection.trigger('requestSchema')`
4. Call `connection.trigger('ready')` to signal to Journey Builder that the activity UI has loaded

Skipping the `ready` handshake or calling `trigger:requestSchema` before `ready` fires causes silent failures where the schema is never populated in the activity's UI.

---

## Common Patterns

### Pattern: Standard Custom Activity with Async Execute

**When to use:** The activity calls an external API or performs work that might exceed a few seconds.

**How it works:**
1. Execute endpoint receives the POST from Journey Builder
2. Validate the JWT in the `Authorization` header using the Installed Package secret
3. Enqueue the real work (e.g., push to a queue, write to a database) — do not perform it synchronously
4. Return HTTP 200 immediately
5. A background worker processes the queued work asynchronously

**Why not the alternative:** Performing the real work synchronously risks exceeding the 30-second timeout. Journey Builder does not retry on timeout; the contact errors out permanently for that journey activation.

### Pattern: Custom Split with Multiple Outcome Branches

**When to use:** The activity needs to route contacts to different journey paths based on a condition (e.g., loyalty tier, purchase history, API response).

**How it works:**
1. Declare outcomes in config.json `metaData.outcomes`:
   ```json
   "outcomes": [
     { "key": "high_value", "label": "High Value" },
     { "key": "standard", "label": "Standard" },
     { "key": "at_risk", "label": "At Risk" }
   ]
   ```
2. Execute endpoint evaluates the contact and returns:
   ```json
   { "branchResult": "high_value" }
   ```
3. Journey Builder routes the contact to the branch connector whose key matches `branchResult`

**Why not the alternative:** Using a Decision Split activity requires data to already be in a Data Extension field. Custom splits allow real-time API-based routing that is not pre-stored in SFMC.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to call an external API during journey and route on result | Custom Split Activity | Only custom splits support runtime branching on live API responses |
| Need to perform a side effect (write data, send to external system) without branching | Standard Custom Activity | Simpler config.json; no outcome keys required |
| Need to define who enters a journey from a non-DE source | Custom Entry Source | Uses same Installed Package App Extension registration; defines entry event schema |
| Execute work takes more than a few seconds | Async pattern: return 200 immediately, enqueue work | Journey Builder 30s timeout causes contact errors if exceeded |
| Multiple Marketing Cloud business units use the same activity | Single Installed Package; scope activity to correct BU | App Extensions are registered per package; BU access is configured in the package settings |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Register the App Extension** — In Marketing Cloud Setup, create or open an Installed Package. Add a new Component of type "Journey Builder Activity." Set the Name, description, and Endpoint URL (the base URL where config.json will be served). Note the client ID and client secret for JWT validation.

2. **Author config.json** — At the endpoint base URL, serve a `config.json` that defines: `name`, `fullName`, `workflowApiVersion` (set to `1.1`), `metaData` (icon, category, outcomes for splits), `configurationArguments` (schema for the data the activity stores), `userInterfaces.configModal` (URL to the hosted web app), and `endpoints` (execute, save, publish, validate URLs). Validate against the Journey Builder Activity Config reference docs.

3. **Build the hosted web app** — Create an HTTPS-accessible web application. Include `postmonger.js` from the Postmonger library. In `customActivity.js`, initialize the Postmonger session, register all event handlers (`ready`, `requestedSchema`, `requestedData`, `requestedInteractionDefaults`, `updatedActivity`), then trigger `ready` to complete the handshake. Implement the UI to collect and display configurationArguments values.

4. **Implement execute endpoint with JWT verification** — Build the server-side route at the configured execute URL. On each POST: extract the JWT from the `Authorization: Bearer <token>` header, verify the signature using the Installed Package secret (HS256 or RS256 depending on version), then process the contact data. For custom splits, determine the correct branch and return `{ "branchResult": "<outcome_key>" }` with HTTP 200. For standard activities, return HTTP 200 with any body.

5. **Implement save, publish, and validate endpoints** — Journey Builder calls these during canvas design and journey activation. `save` is called when the practitioner saves activity config (return 200 to accept). `publish` is called when the journey activates (return 200 to confirm the activity is ready). `validate` is called to check if activity configuration is complete (return 200 with a validation result object).

6. **Test end-to-end in a test journey** — Create a journey in a sandbox/test Marketing Cloud BU using the custom activity. Use a small test audience. Verify contacts flow through the activity, check journey activity logs for errors, and confirm any external side effects occurred correctly.

7. **Verify JWT validation and HTTPS** — Confirm the execute endpoint rejects requests without a valid JWT (return 401 or 403). Confirm all endpoints are HTTPS. Confirm no HTTP fallback is allowed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] config.json is served over HTTPS and is valid JSON with all required keys (name, workflowApiVersion, metaData, endpoints, userInterfaces)
- [ ] customActivity.js listens for `ready` before calling any `connection.trigger()` methods
- [ ] Execute endpoint verifies the JWT from the Authorization header before processing
- [ ] Execute endpoint returns HTTP 200 within 30 seconds (or configured timeout); long operations are enqueued asynchronously
- [ ] For custom splits: all outcome keys in `branchResult` responses exactly match keys declared in config.json `metaData.outcomes`
- [ ] All URLs in config.json (userInterfaces, endpoints) use HTTPS
- [ ] save, publish, and validate endpoints are implemented and return HTTP 200
- [ ] Tested with a real contact in a test journey; journey activity logs show no errors

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Non-200 response errors the contact permanently** — Any HTTP response other than 200 from the execute endpoint causes Journey Builder to mark that contact's journey activation as errored. The contact does not get a retry and does not advance. This includes 201, 202, 204, and any 4xx/5xx. Return exactly HTTP 200.

2. **Postmonger `ready` event must fire before any trigger calls** — If customActivity.js calls `connection.trigger('requestSchema')` before Journey Builder fires the `ready` event, the call is silently dropped. The schema is never returned and the UI has no field mappings. Always register listeners first, then call `connection.trigger('ready')` and wait.

3. **config.json must be reachable without authentication** — Journey Builder fetches config.json at design time from the URL registered in the App Extension. If the endpoint requires authentication or returns a non-200, the activity will fail to load on the canvas. Serve config.json as a public, unauthenticated GET endpoint.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| config.json | Application extension definition served at the registered endpoint base URL |
| customActivity.js | Postmonger-based cross-frame messaging script loaded in the activity iframe |
| Hosted web app | HTTPS-accessible UI application serving the activity configuration panel |
| Execute endpoint | Server-side route that receives Journey Builder POSTs and returns HTTP 200 with optional branchResult |
| JWT validation logic | Middleware verifying the Installed Package JWT on every inbound execute request |

---

## Related Skills

- **admin/journey-builder-administration** — Use when the issue is with the Journey Builder canvas, entry source configuration, journey settings, or standard activity setup rather than custom activity code
- **apex/marketing-cloud-rest-api** — Use when working with the Marketing Cloud REST API for data operations outside of the Journey Builder custom activity framework
