# Gotchas — Marketing Cloud API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Journey Injection Returns 201 Even When the Contact Is Silently Dropped

**What happens:** The `/interaction/v1/events` endpoint returns HTTP 201 (Created) even when the contact fails to enter the journey due to a field name mismatch, a missing required field, or an inactive journey version. There is no error in the response body. The contact simply never appears in Journey Builder's contact history.

**When it occurs:** Any time the `Data` object contains field names that do not exactly match the entry source schema — including case sensitivity. For example, if the entry source schema defines `AccountTier`, sending `accountTier` or `account_tier` causes a silent drop. Also occurs when the journey is in Draft or Stopped status or when the EventDefinitionKey is the journey key rather than the entry source key.

**How to avoid:** After firing injection events in a test environment, always verify contact entry in Journey Builder under the journey's "Contact History" or "Activity" view. Never rely solely on the 201 response as confirmation of successful entry. Cross-check every `Data` field name against the exact entry source schema configuration before going to production.

---

## Gotcha 2: TriggeredSendDefinition Must Be in Active/Started Status — Draft Status Returns a Silent Failure

**What happens:** Attempting to fire a triggered send against a TriggeredSendDefinition that is in `Draft` or `Paused` status returns an API error. The error message from Marketing Cloud ("Unable to queue message") does not clearly state that the definition status is the cause. Practitioners often assume the ExternalKey or credentials are wrong and waste time debugging the wrong thing.

**When it occurs:** Any time a TriggeredSendDefinition is created (defaults to Draft) but not explicitly started before the first send attempt. Also occurs after a definition is intentionally paused and someone fires a send without restarting it.

**How to avoid:** Always verify the TriggeredSendDefinition status in Marketing Cloud Setup → Email Studio → Triggered Sends before making the first API call. The status must be `Running` (shown as "Active" in the UI). Use the SOAP API `TriggeredSend` object's `TriggeredSendStatus` property or check the UI directly. Include a status check in the integration's pre-flight validation.

---

## Gotcha 3: OAuth Tokens Are Tenant-Specific and Cannot Be Shared Across Business Units

**What happens:** In a multi-Business-Unit Marketing Cloud org, an OAuth token acquired using one Business Unit's Installed Package cannot be used to call API endpoints for a different Business Unit. The token is scoped to the BU (identified by the MID) associated with the Installed Package. Using a token from BU A to write to a DE in BU B returns a 403 or a "permission denied" error with no clear indication the problem is cross-BU token scope.

**When it occurs:** When a single Salesforce integration tries to write to DEs or inject into journeys across multiple Marketing Cloud Business Units using one set of credentials. Common in enterprise orgs with regional BU segmentation.

**How to avoid:** Create a separate Installed Package with API Integration in each Business Unit that the integration needs to call. Store each BU's Client ID, Client Secret, and subdomain separately (e.g., per-BU Custom Metadata records). Acquire and use the token for the specific target BU for each API call.

---

## Gotcha 4: The EventDefinitionKey Is Not the Journey Key

**What happens:** Practitioners look up the Journey key in Journey Builder and use it as the `EventDefinitionKey` in the `/interaction/v1/events` payload. The API returns a 400 error with a message like "Invalid EventDefinitionKey" — or in some versions, a 404. The Journey key and the entry source's EventDefinitionKey are different identifiers.

**When it occurs:** Any time a developer looks at the Journey URL or Journey properties to get an identifier, rather than navigating to the journey's specific entry source settings.

**How to avoid:** In Journey Builder, open the journey and click on the entry source (the API entry event block). The `EventDefinitionKey` is shown in the entry source's settings panel — it follows the format `APIEvent-{{GUID}}`. This is the only correct value for the `EventDefinitionKey` field in the injection request.

---

## Gotcha 5: Async DE Insert RequestId Expiry — Status Is Not Permanently Available

**What happens:** The status endpoint `GET /hub/v1/dataeventsasync/{requestId}` does not retain results indefinitely. If the polling call is delayed too long after job completion, the status may no longer be available and the endpoint returns an error or empty response, making it impossible to confirm whether the rows were committed successfully.

**When it occurs:** When batch processing jobs submit async DE rows and then delay polling by hours (e.g., polling the next day in a scheduled job). The exact retention window is not published in documentation but is known from practitioner experience to be short (minutes to low hours).

**How to avoid:** Poll the `requestId` status within minutes of submission, not hours. Design the async DE upsert workflow to poll immediately after submitting all chunks, before the Apex or job context is released. Store the `requestId` values with a job timestamp and alert if any remain unpolled after more than 15 minutes.
