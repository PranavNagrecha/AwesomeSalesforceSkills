# Gotchas — Service Cloud REST API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Data Category Developer Name Mismatch Returns HTTP 200 with Empty Results

**What happens:** When a `categoryGroup` or `category` query parameter value does not match an existing data category developer name — including wrong case, using the label instead of the developer name, or a typo — the Knowledge REST API returns HTTP 200 with `{"articles": [], "total": 0}`. No error is raised. The response is identical to a valid query that genuinely has no matching articles.

**When it occurs:** Any call to `/knowledgeManagement/articles?categoryGroup=X&category=Y` or `/support/knowledgeWithSEO/articles?categoryGroup=X&category=Y` where the developer name is wrong. Common triggers: using the label ("My Products") instead of the developer name ("My_Products"), case mismatch ("products" vs. "Products"), or referencing a category that has been renamed in Setup without updating the integration.

**How to avoid:**
- Always verify developer names in Setup > Data Categories, not labels.
- Add a dedicated integration test that asserts the article count is greater than zero for a known-populated category, so a category rename surfaces as a test failure immediately.
- Log the `total` field from the response alongside the category names for observability — a persistent zero total with known-good data is a signal the category name is wrong.

---

## Gotcha 2: Legacy Chat REST API Is Permanently Retired (February 14, 2026)

**What happens:** All calls to the legacy Salesforce Chat REST API (`<instance>.salesforce.com/chat/rest/`) return HTTP errors after the retirement date. This includes session initialization (`/System/SessionId`), chat initiation (`/Chasitor/ChasitorInit`), and the message polling loop (`/System/Messages`). Salesforce does not provide a compatibility shim or forwarding redirect.

**When it occurs:** Any org or external system that was built against the legacy Chat REST API and has not completed migration to the Messaging for In-App and Web (MIAW) Enhanced Chat API. This affects custom web chat widgets, mobile apps using the LiveAgent SDK, and back-end middleware that used the legacy API for bot handoffs or transcript streaming.

**How to avoid:**
- Audit all codebases for `/chat/rest/` and `X-LIVEAGENT-API-VERSION` header usage.
- If the retirement date has passed, treat this as an emergency incident — migrate to MIAW immediately.
- For new implementations, use only the MIAW Enhanced Chat API from the start. Do not use legacy Chat REST in new development even if the org has not yet migrated existing channels.

---

## Gotcha 3: `/knowledgeManagement/` Requires Authentication — It Does Not Work for Guest Users

**What happens:** The `/knowledgeManagement/` endpoint family requires a valid authenticated Salesforce session. When called from an Experience Cloud page in a guest user context (either without a token or with a guest session token), the API returns HTTP 401. Developers building self-service portals who accidentally use this endpoint instead of `/support/knowledgeWithSEO/` get consistent authentication failures that look like a permissions issue.

**When it occurs:** LWC components or Apex controllers in Experience Cloud guest contexts that target `/knowledgeManagement/` instead of `/support/knowledgeWithSEO/`. Also occurs when developers copy-paste Apex from an internal agent tool and use it on a public portal without adjusting the endpoint.

**How to avoid:**
- Use `/support/knowledgeWithSEO/` exclusively for any Experience Cloud or public-facing article retrieval.
- Enforce the rule: if the page is accessible without login, the Knowledge endpoint must be `/support/knowledgeWithSEO/`.

---

## Gotcha 4: Guest User Data Category Visibility Is a Separate Configuration From Article Publish Status

**What happens:** Even when a Knowledge article is published and the Experience Cloud site is correctly configured, `/support/knowledgeWithSEO/` returns an empty result for guest users if the guest user profile has not been explicitly granted data category visibility. The API does not return a permission error — it returns an empty array, which is indistinguishable from "no articles in that category."

**When it occurs:** When a Salesforce admin publishes articles and sets up an Experience Cloud site but omits the step of configuring Data Category Visibility for the guest user profile (Setup > Users > Profiles > [Guest Profile] > Data Category Visibility). Affects organizations that add new data category groups without updating guest profile visibility.

**How to avoid:**
- After setting up a new data category group, immediately add it to the guest user profile's Data Category Visibility settings.
- Add a post-deployment verification step: make a test call to `/support/knowledgeWithSEO/` from an unauthenticated HTTP client and confirm articles are returned before marking a deployment complete.

---

## Gotcha 5: URL-Name Lookup Is Not Unique Across Article Types

**What happens:** The `urlName` field on Knowledge articles is unique within an article type, but not enforced as globally unique across all article types. When two articles of different types share the same `urlName`, a query to `/support/knowledgeWithSEO/articles?urlName=<slug>` may return both articles. The response order is not deterministic, so code that assumes `articles[0]` is always the correct article can return the wrong content intermittently.

**When it occurs:** Orgs with multiple Knowledge article types that were created before Salesforce enforced global URL-name uniqueness, or orgs that manually assigned the same URL-name string to articles of different types. More common in orgs that have been on Salesforce Knowledge for many years.

**How to avoid:**
- Audit for duplicate URL names across article types using a SOQL query: `SELECT UrlName, COUNT(Id) c FROM Knowledge__kav WHERE PublishStatus = 'Online' GROUP BY UrlName HAVING COUNT(Id) > 1`.
- When multiple results are returned by the URL-name lookup, add article-type filtering via the `articleType` query parameter.
- For new article creation workflows, enforce global URL-name uniqueness as an org policy and add a validation rule or Process Builder check.
