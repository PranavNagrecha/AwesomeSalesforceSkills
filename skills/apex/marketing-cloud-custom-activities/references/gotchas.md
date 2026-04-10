# Gotchas — Marketing Cloud Custom Activities

Non-obvious Salesforce Marketing Cloud platform behaviors that cause real production problems in this domain.

## Gotcha 1: HTTP-Only Endpoints Cause Silent Load Failure

**What happens:** Journey Builder refuses to load the activity configuration UI (the iframe) and silently fails to register the activity on the canvas if any URL in config.json uses `http://` instead of `https://`. There is no explicit error message in the Journey Builder canvas — the activity panel simply does not open, or the canvas displays a generic "activity unavailable" state.

**When it occurs:** Any time the hosted web app, execute endpoint, or any URL registered in config.json uses plain HTTP. This includes development environments where a local tunnel (ngrok, localtunnel) is used without HTTPS. It also occurs if TLS certificates expire on the hosting infrastructure.

**How to avoid:** Provision TLS on all hosting infrastructure before connecting the App Extension. For local development, use ngrok with HTTPS tunnels (`ngrok http 3000` provides an `https://` URL by default). Validate all URLs in config.json start with `https://` as part of the review checklist. Set up TLS certificate expiry alerting for production hosts.

---

## Gotcha 2: branchResult Key Mismatch Errors the Contact Silently

**What happens:** If the execute endpoint for a custom split activity returns a `branchResult` value that does not exactly match one of the outcome keys declared in config.json `metaData.outcomes`, Journey Builder cannot route the contact to any branch. The contact is marked as errored and removed from the journey. This failure does not surface as a visible error on the journey canvas in real time — it appears only in the journey activity error logs, which require explicit investigation.

**When it occurs:** Most commonly caused by case sensitivity mismatches (config.json declares `"Gold"` but execute endpoint returns `"gold"`), typos in outcome keys, or when config.json is updated to rename/remove an outcome key without updating the execute endpoint logic.

**How to avoid:** Define outcome keys as lowercase constants shared between config.json and execute endpoint code — ideally sourced from the same configuration file or environment variable. Add an integration test that exercises every declared outcome key end-to-end. When updating outcome keys in config.json, treat it as a breaking change: update the execute endpoint in the same deployment.

---

## Gotcha 3: Journey Builder Does Not Retry on Execute Timeout

**What happens:** If the execute endpoint does not return HTTP 200 within the configured timeout window (default 30 seconds), Journey Builder marks the contact as errored and does not retry. Unlike some message queuing systems, Journey Builder has no built-in retry mechanism for custom activity timeouts. The contact's journey activation is permanently in an error state for that run.

**When it occurs:** Any time the execute endpoint performs synchronous long-running work (API calls, database queries, file operations) that occasionally exceeds the timeout. Peak load periods are the most common trigger. Third-party API latency spikes are another common cause.

**How to avoid:** Design the execute endpoint to return HTTP 200 immediately after validating the JWT and enqueuing the work. Perform all real processing in a background worker. Apply an internal timeout on any downstream API calls (shorter than the Journey Builder timeout) and fail fast with a fallback rather than letting the call hang. If a longer journey timeout is needed, it can be configured in config.json `endpoints.execute.timeout` (in milliseconds), but this should be a last resort, not a substitute for async design.

---

## Gotcha 4: config.json Is Fetched Unauthenticated at Design Time

**What happens:** Journey Builder fetches config.json using a plain unauthenticated HTTP GET whenever a practitioner loads the Journey Builder canvas. If the config.json endpoint requires authentication (an API key, OAuth token, or IP allowlist), Journey Builder receives a 401 or 403 response, fails to parse the activity definition, and the activity does not appear on the canvas or appears in a broken state.

**When it occurs:** When developers apply the same authentication middleware to all routes including the config.json route, or when production network rules restrict ingress to known IP ranges (Journey Builder's IP is Salesforce infrastructure and may not be in an allowlist).

**How to avoid:** Serve config.json as a public, unauthenticated GET endpoint. The file itself contains no secrets — it is a static definition. Authentication belongs on the execute, save, publish, and validate endpoints (via JWT verification), not on config.json. If a WAF or IP allowlist is in place, explicitly exclude the config.json route from auth rules.

---

## Gotcha 5: updatedActivity Fires on Every Canvas Save, Not Just on "Done"

**What happens:** The Postmonger `updatedActivity` event fires every time Journey Builder saves the activity's state, including auto-saves triggered by the canvas. This means `updatedActivity` can fire multiple times during a single editing session. If the event handler performs expensive operations (API calls, full UI re-renders) on every fire, the configuration panel becomes sluggish or makes unnecessary external calls.

**When it occurs:** During any editing session where the practitioner interacts with the Journey Builder canvas while the activity configuration panel is open. Auto-save frequency increases if the journey has many activities.

**How to avoid:** In the `updatedActivity` handler, store the received activity object in a local variable and debounce or compare against the previous value before performing expensive operations. Only persist or sync configuration when the activity data has actually changed from the last known state.
