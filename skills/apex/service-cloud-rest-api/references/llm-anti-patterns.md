# LLM Anti-Patterns — Service Cloud REST API

Common mistakes AI coding assistants make when generating or advising on Service Cloud REST API integrations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `/knowledgeManagement/` for Guest or Portal Contexts

**What the LLM generates:** Apex controllers or LWC code for Experience Cloud guest pages that call `/services/data/vXX.X/knowledgeManagement/articles` — the authoring endpoint — instead of `/services/data/vXX.X/support/knowledgeWithSEO/articles`.

**Why it happens:** Training data contains more examples of authenticated internal-user Knowledge API usage than guest/portal usage. The authoring endpoint is more commonly documented in general Apex integration tutorials. LLMs generalize from the more common pattern without recognizing the authentication context difference.

**Correct pattern:**

```
// For unauthenticated guest / Experience Cloud visitor:
GET /services/data/v62.0/support/knowledgeWithSEO/articles?categoryGroup=X&category=Y

// For authenticated agent / internal user:
GET /services/data/v62.0/knowledgeManagement/articles?categoryGroup=X&category=Y
```

**Detection hint:** Look for `/knowledgeManagement/` in Apex classes annotated `@AuraEnabled` that are used in Experience Cloud pages or that have `without sharing` and are intended for guest users.

---

## Anti-Pattern 2: Treating Legacy Chat REST API as Still Active

**What the LLM generates:** New Apex or JavaScript code that calls `/chat/rest/System/SessionId`, uses `X-LIVEAGENT-API-VERSION` headers, or implements the `GET /chat/rest/System/Messages` long-polling pattern as if the legacy Chat REST API is a valid current option.

**Why it happens:** The legacy Chat REST API was documented for many years and appears frequently in training data. LLMs with knowledge cutoffs before February 14, 2026 (the retirement date) may not know the API is retired. Even post-cutoff models may revert to the well-represented legacy pattern when given ambiguous prompts.

**Correct pattern:**

```
// WRONG — retired Feb 14, 2026:
GET https://<instance>.salesforce.com/chat/rest/System/SessionId
X-LIVEAGENT-API-VERSION: 52
X-LIVEAGENT-AFFINITY: null

// CORRECT — use Enhanced Chat API (MIAW):
// Provision via Setup > Messaging Settings (In-App and Web)
// Authenticate via OAuth 2.0 Connected App
// Use Platform Events / MIAW SDK for conversation streaming
```

**Detection hint:** Search generated code for `/chat/rest/`, `X-LIVEAGENT-API-VERSION`, `X-LIVEAGENT-SESSION-KEY`, `ChasitorInit`, or `LiveAgent`. Any of these strings indicates the legacy Chat REST API.

---

## Anti-Pattern 3: Using Data Category Labels Instead of Developer Names in Query Parameters

**What the LLM generates:** REST API calls that use human-readable category labels (e.g., `?categoryGroup=My Products&category=Laptop Accessories`) in query parameters instead of developer names (e.g., `?categoryGroup=My_Products&category=Laptop_Accessories`).

**Why it happens:** LLMs default to the user-visible string they are most likely to know from context (the label shown in the UI or in user stories). The distinction between label and developer name is a Salesforce-specific concept that LLMs frequently collapse to a single string.

**Correct pattern:**

```
// WRONG — uses label (space, different case):
?categoryGroup=My Products&category=Laptop Accessories

// CORRECT — uses developer name (underscore, exact case from Setup):
?categoryGroup=My_Products&category=Laptop_Accessories
```

**Detection hint:** If the category query parameter value contains spaces or does not match the format expected in Setup > Data Categories > [Group] > Developer Name column, flag it. Verify by cross-referencing against the Setup-visible developer names.

---

## Anti-Pattern 4: Ignoring the Empty-Array Silent Failure Case

**What the LLM generates:** Apex code that calls a Knowledge REST endpoint and immediately iterates over `articles` without checking whether the array is empty, treating a zero-result response identically to a successful filtered result.

**Why it happens:** LLMs model the "happy path" most commonly seen in training examples. The Knowledge REST API returning HTTP 200 with an empty array for an invalid category is a Salesforce-specific behavior that does not follow the convention of returning an error code for bad input. LLMs do not anticipate this silent failure mode.

**Correct pattern:**

```apex
// WRONG — no empty-result handling:
List<Object> articles = (List<Object>) body.get('articles');
for (Object item : articles) { ... } // NullPointerException if articles is null

// CORRECT — explicit empty-result handling:
List<Object> articles = (List<Object>) body.get('articles');
if (articles == null || articles.isEmpty()) {
    // Log warning: possibly wrong category name or no visibility
    System.debug(LoggingLevel.WARN, 'No articles returned. Verify category developer name.');
    return new List<Map<String, Object>>();
}
for (Object item : articles) { ... }
```

**Detection hint:** Look for `body.get('articles')` followed immediately by iteration without a null/empty check. Also look for code that treats an empty result as an error (throws exception) rather than handling it as a valid state.

---

## Anti-Pattern 5: Hardcoding Article Record IDs Instead of URL Names for Article Links

**What the LLM generates:** Article detail page URLs or cross-reference links that embed a Salesforce record ID (e.g., `?id=kA0xx000000XXXXX`) rather than using the article's stable URL name.

**Why it happens:** LLMs default to using the record ID as the unique identifier for Salesforce records, which is the general pattern for most Salesforce objects. LLMs are less likely to know that Knowledge article IDs are version-specific and change on re-publication, making them unsuitable as stable permalinks.

**Correct pattern:**

```
// WRONG — ID-based link, breaks on re-publication:
/s/article?id=kA0xx000000XXXXX

// CORRECT — URL-name-based link, stable across versions:
/s/article/how-to-reset-password
// backed by: GET /support/knowledgeWithSEO/articles?urlName=how-to-reset-password
```

**Detection hint:** Look for links or API calls containing 15- or 18-character Salesforce IDs in Knowledge article URLs. Article IDs typically start with `kA0` or `kA1` in production orgs. Any hardcoded ID in a URL pointing to a Knowledge article is a signal to replace with URL-name lookup.

---

## Anti-Pattern 6: Missing URL-Encoding on Category Query Parameters

**What the LLM generates:** String concatenation to build Knowledge REST API query URLs that does not URL-encode the `categoryGroup` and `category` parameter values before appending them to the endpoint string.

**Why it happens:** LLMs frequently generate string interpolation for URL construction without applying URL encoding, especially for parameters that "look clean" (short words, no obvious special characters). Category developer names with underscores are safe, but developer names with special characters or spaces cause malformed URLs.

**Correct pattern:**

```apex
// WRONG — no URL encoding:
String endpoint = baseUrl + '/knowledgeManagement/articles?categoryGroup=' + categoryGroup
    + '&category=' + categoryName;

// CORRECT — URL-encoded parameters:
String endpoint = baseUrl + '/knowledgeManagement/articles'
    + '?categoryGroup=' + EncodingUtil.urlEncode(categoryGroup, 'UTF-8')
    + '&category=' + EncodingUtil.urlEncode(categoryName, 'UTF-8');
```

**Detection hint:** Look for string concatenation building a REST API URL where the parameter values come from variables and are not wrapped in `EncodingUtil.urlEncode(...)`.
