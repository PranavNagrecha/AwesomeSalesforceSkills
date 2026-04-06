# Examples — Service Cloud REST API

## Example 1: Authenticated Knowledge Article Retrieval Filtered by Data Category

**Context:** A case management Visualforce page or LWC (authenticated agent context) needs to surface relevant Knowledge articles based on the case's product category. The articles must be filtered to a specific data category and returned as JSON for display.

**Problem:** Developers unfamiliar with Service Cloud REST API use SOQL directly on `Knowledge__kav`, which does not honor data category visibility rules and does not support URL-name lookups. The SOQL approach also returns draft articles unless `PublishStatus = 'Online'` is explicitly added, leading to agents seeing unpublished content.

**Solution:**

```apex
public class KnowledgeArticleRetriever {

    public static List<Map<String, Object>> getArticlesByCategory(
        String categoryGroup,
        String categoryName,
        Integer pageSize
    ) {
        String baseUrl = URL.getOrgDomainUrl().toExternalForm();
        String endpoint = baseUrl
            + '/services/data/v62.0/knowledgeManagement/articles'
            + '?categoryGroup=' + EncodingUtil.urlEncode(categoryGroup, 'UTF-8')
            + '&category=' + EncodingUtil.urlEncode(categoryName, 'UTF-8')
            + '&pageSize=' + pageSize
            + '&publishStatus=Online';

        HttpRequest req = new HttpRequest();
        req.setEndpoint(endpoint);
        req.setMethod('GET');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        req.setHeader('Accept', 'application/json');

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() != 200) {
            throw new CalloutException(
                'Knowledge API error ' + res.getStatusCode() + ': ' + res.getBody()
            );
        }

        Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        List<Object> rawArticles = (List<Object>) body.get('articles');

        // Handle silent empty-result case from bad category names
        if (rawArticles == null || rawArticles.isEmpty()) {
            return new List<Map<String, Object>>();
        }

        List<Map<String, Object>> articles = new List<Map<String, Object>>();
        for (Object item : rawArticles) {
            articles.add((Map<String, Object>) item);
        }
        return articles;
    }
}
```

**Why it works:** The request uses `UserInfo.getSessionId()` for the Bearer token (valid in synchronous Apex), URL-encodes the category parameters to handle spaces and special characters, explicitly filters to `publishStatus=Online` to avoid returning drafts, and handles the empty-array response that occurs when a category name is invalid or no articles are visible.

---

## Example 2: Unauthenticated Guest Article Lookup by URL Name (Experience Cloud)

**Context:** An Experience Cloud self-service portal renders Knowledge article detail pages using the article's URL name as the route parameter (e.g., `/help/articles/how-to-reset-password`). The LWC must fetch the article body without requiring the visitor to log in.

**Problem:** Teams attempt to use `/knowledgeManagement/articles` with a Connected App token on the guest path, which fails because the authoring endpoint requires an authenticated internal-user session and would expose unpublished articles. Some teams hardcode the article ID from the URL path, which changes on article re-publication and breaks bookmarked URLs.

**Solution:**

```apex
// Apex controller for Experience Cloud guest user context
// Class must be marked 'without sharing' for guest callout —
// data category visibility is enforced by the API itself, not Apex sharing.
public without sharing class GuestKnowledgeController {

    @AuraEnabled(cacheable=true)
    public static Map<String, Object> getArticleByUrlName(String urlName) {
        if (String.isBlank(urlName)) {
            throw new AuraHandledException('urlName is required');
        }

        String baseUrl = URL.getOrgDomainUrl().toExternalForm();
        // v44+ required for urlName parameter support
        String endpoint = baseUrl
            + '/services/data/v62.0/support/knowledgeWithSEO/articles'
            + '?urlName=' + EncodingUtil.urlEncode(urlName.trim(), 'UTF-8');

        HttpRequest req = new HttpRequest();
        req.setEndpoint(endpoint);
        req.setMethod('GET');
        // Guest context: no Authorization header; API uses the site guest user session
        req.setHeader('Accept', 'application/json');

        Http http = new Http();
        HttpResponse res;
        try {
            res = http.send(req);
        } catch (System.CalloutException e) {
            throw new AuraHandledException('Callout failed: ' + e.getMessage());
        }

        if (res.getStatusCode() != 200) {
            throw new AuraHandledException(
                'Knowledge guest API error ' + res.getStatusCode()
            );
        }

        Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        List<Object> articles = (List<Object>) body.get('articles');

        if (articles == null || articles.isEmpty()) {
            return null; // Article not found or not visible to guest
        }

        // Return first match; warn if multiple matches (non-unique urlName)
        if (articles.size() > 1) {
            System.debug(LoggingLevel.WARN,
                'Multiple articles match urlName: ' + urlName + ' — returning first result.');
        }
        return (Map<String, Object>) articles.get(0);
    }
}
```

**Why it works:** The `/support/knowledgeWithSEO/` endpoint handles the guest user session automatically in an Experience Cloud context without requiring an explicit Authorization header. The URL-name parameter is available from API v62.0 (Spring '25) and was introduced in v44. The method returns `null` on empty results rather than throwing an exception, allowing the LWC to render a "not found" state cleanly.

---

## Anti-Pattern: Using Legacy Chat REST API After Retirement

**What practitioners do:** Teams with existing middleware or mobile apps built against the legacy Chat REST API (`/chat/rest/System/SessionId`, `X-LIVEAGENT-API-VERSION` header) continue using those integrations post-February 14, 2026, or attempt to wrap them in a proxy to extend their life.

**What goes wrong:** The legacy Chat REST API endpoint was permanently retired on February 14, 2026. All calls to `/chat/rest/` after that date return HTTP errors. Proxy wrappers that attempt to relay calls to the retired endpoint inherit the same failure. There is no backward-compatible shim provided by Salesforce.

**Correct approach:** Migrate to Messaging for In-App and Web (MIAW) Enhanced Chat API. Key steps:
1. Provision an Enhanced Messaging Channel in Setup > Messaging Settings (In-App and Web type).
2. Replace `X-LIVEAGENT-*` header-based session initiation with OAuth 2.0 Connected App authentication.
3. Replace the long-poll `GET /chat/rest/System/Messages` loop with Platform Event subscription or the MIAW SDK.
4. Map `LiveChatTranscript` records to `MessagingSession` records for reporting continuity.
5. Update routing logic in Omni-Channel to use the new Messaging Channel instead of the legacy Chat button.
