# Gotchas — MCAE (Pardot) API v5

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Missing `Pardot-Business-Unit-Id` Returns 401, Not a Descriptive Error

**What happens:** Every API v5 request that omits the `Pardot-Business-Unit-Id` header returns HTTP 401 Unauthorized. The response body says the request is unauthorized but does not mention the missing header. This is indistinguishable from an expired or invalid OAuth token, causing developers to waste significant time regenerating tokens, recreating Connected Apps, or checking user permissions.

**When it occurs:** Any time the header is omitted from an HTTP client — common when copying request patterns from v3/v4 documentation (which did not require this header) or when middleware strips custom headers.

**How to avoid:** Add `Pardot-Business-Unit-Id` as a required header in your HTTP client base configuration or interceptor so it cannot be accidentally omitted. The BU ID is found in Account Engagement Settings > Account Settings > Business Unit ID. Validate the header is present before debugging any 401.

---

## Gotcha 2: POST to Prospect Silently Upserts — No 409 Conflict Error

**What happens:** If you POST a new Prospect with an email address that already exists in the business unit, the API does not return an error. It silently updates the existing Prospect record and returns the existing record's `id` with a 200 response. This means the caller cannot distinguish between a create and an update from the status code alone.

**When it occurs:** During bulk imports, migration scripts, or event-driven flows where the existence of the prospect is not pre-checked. This can cause unexpected overwrites of existing field values — for example, a marketing source field gets overwritten by the new POST payload.

**How to avoid:** If you need to distinguish creates from updates, query the Prospect by email first (`GET /prospects?email=...&fields=id`) and check whether a result is returned. If preserving existing field values is critical, only include the fields you intend to change in the POST body. Alternatively, use PATCH with the Prospect `id` for intentional updates.

---

## Gotcha 3: Offset Pagination Is Silently Ignored — nextPageMark Required

**What happens:** If you include a `page` or `offset` query parameter in a v5 list request (patterns common in v3/v4 and many third-party REST APIs), the parameter is ignored and the API always returns the first page. There is no error — the response is valid JSON with the first page of results. This causes infinite loops in pagination code that increments `page` but always receives the same data.

**When it occurs:** When migrating code from API v3/v4, or when a developer uses a generic paginator that assumes offset-based pagination.

**How to avoid:** Use `nextPageMark` exclusively. After each response, check for the presence of `nextPageMark` in the response envelope. If present, include it as a query parameter in the next request. If absent, you have reached the last page. Do not use `page`, `offset`, or similar parameters.

---

## Gotcha 4: Visitor Records Cannot Be Queried by Email or Name

**What happens:** Visitors are anonymous session records tied to a tracking cookie. The Visitor object in the API does not expose email as a filterable field. Requests like `GET /visitors?email=user@example.com` return empty results or a 400 validation error — not a useful match.

**When it occurs:** When a practitioner wants to find all sessions for a known contact and conflates the Visitor object with the Prospect object. Prospects are identified by email; Visitors are identified by cookie/session.

**How to avoid:** To retrieve engagement events for a known Prospect, use the VisitorActivity object filtered by `prospectId`. Once a Visitor is converted (via form submission or email click), it is linked to a Prospect, and all their activity is accessible through VisitorActivities. The Visitor record itself is rarely the right object to query directly.

---

## Gotcha 5: API v5 Uses JSON Only — v3/v4 XML Patterns Break

**What happens:** API v3 and v4 returned XML by default and required an `output=json` query parameter for JSON. API v5 uses JSON exclusively. Code that sends `Accept: application/xml` headers or appends `output=json` to v5 URLs either receives an error or gets unexpected behavior. The response format from v5 is always JSON.

**When it occurs:** When migrating or combining v3/v4 code patterns with a v5 endpoint. Also occurs when a generic client sets `Accept: application/xml` globally.

**How to avoid:** Always set `Content-Type: application/json` and `Accept: application/json` for v5 requests. Remove `output=json`, `output=bulk`, and similar legacy query parameters — they are not recognized by v5. Audit any copied code from v3/v4 documentation for XML-related patterns.

---

## Gotcha 6: Visitor Activity `type` Field Is an Integer Code, Not a String Label

**What happens:** The `type` field on a VisitorActivity record is an integer (e.g., `1`, `4`, `6`), not a human-readable string like `"email_click"` or `"form_submission"`. Code that compares `activity.type == "form_submission"` will always evaluate to false, causing filter logic to silently fail.

**When it occurs:** When building dashboards or ETL pipelines that need to categorize activities by type. The API response includes both `type` (integer) and `typeName` (string) if you request the `typeName` field explicitly.

**How to avoid:** Always request `typeName` in your `fields` parameter (e.g., `?fields=id,type,typeName,createdAt`) so you have both the code and the label. Common type codes: 1 = email click, 4 = form submission, 6 = page view, 10 = email open, 11 = custom redirect, 13 = file download. Document the mapping in your integration.
