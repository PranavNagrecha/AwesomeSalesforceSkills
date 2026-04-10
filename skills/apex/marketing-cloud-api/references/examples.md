# Examples — Marketing Cloud API

## Example 1: Apex Callout — Inject Contact into Journey After Opportunity Close

**Context:** A sales team closes an Opportunity and wants the customer automatically injected into a Marketing Cloud onboarding journey. The journey is triggered via an API entry source. The Apex code runs in an after-update trigger on Opportunity.

**Problem:** Without structured token caching and correct field mapping, either the token endpoint is hammered per record (rate limit exhaustion), or the contact is silently dropped because field names in the `Data` object do not match the journey entry source schema.

**Solution:**

```apex
public class MCJourneyInjector {

    // Store credentials in Custom Metadata — never hardcode
    private static final String SUBDOMAIN = MC_Config__mdt.getInstance('Default').Subdomain__c;
    private static final String CLIENT_ID = MC_Config__mdt.getInstance('Default').ClientId__c;
    private static final String CLIENT_SECRET = MC_Config__mdt.getInstance('Default').ClientSecret__c;

    // Acquire OAuth 2.0 bearer token using client credentials flow
    public static String getAccessToken() {
        HttpRequest tokenReq = new HttpRequest();
        tokenReq.setEndpoint('https://' + SUBDOMAIN + '.auth.marketingcloudapis.com/v2/token');
        tokenReq.setMethod('POST');
        tokenReq.setHeader('Content-Type', 'application/json');
        tokenReq.setBody(JSON.serialize(new Map<String, String>{
            'grant_type'    => 'client_credentials',
            'client_id'     => CLIENT_ID,
            'client_secret' => CLIENT_SECRET
        }));

        Http http = new Http();
        HttpResponse res = http.send(tokenReq);

        if (res.getStatusCode() != 200) {
            throw new CalloutException('MC token acquisition failed: ' + res.getBody());
        }

        Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        return (String) body.get('access_token');
    }

    // Inject a contact into a journey
    // EventDefinitionKey must be from the journey entry source settings, NOT the journey key
    public static void fireEntryEvent(String contactKey, String eventDefinitionKey,
                                      Map<String, Object> dataFields) {
        String token = getAccessToken();

        Map<String, Object> payload = new Map<String, Object>{
            'ContactKey'       => contactKey,
            'EventDefinitionKey' => eventDefinitionKey,
            'Data'             => dataFields
        };

        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://' + SUBDOMAIN + '.rest.marketingcloudapis.com/interaction/v1/events');
        req.setMethod('POST');
        req.setHeader('Authorization', 'Bearer ' + token);
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(payload));

        Http http = new Http();
        HttpResponse res = http.send(req);

        // HTTP 201 = accepted. It does NOT guarantee the contact entered the journey.
        // Field name mismatches cause silent drops with a 201 response.
        if (res.getStatusCode() != 201) {
            throw new CalloutException('Journey injection failed: ' + res.getBody());
        }
    }
}
```

**Why it works:** Credentials are stored in Custom Metadata (not hardcoded). The `Data` map is built with field names that exactly match the journey entry source schema — case-sensitively. The code checks the HTTP status code and throws on non-201 responses, while acknowledging that 201 only means the request was accepted, not that the contact entered the journey.

---

## Example 2: Bulk Data Extension Row Upsert Using Async Endpoint

**Context:** A nightly batch job in Salesforce needs to sync 5,000 Account records into a Marketing Cloud Data Extension to keep the audience list current for segmentation campaigns.

**Problem:** Using the synchronous `/hub/v1/dataevents` endpoint for 5,000 rows causes Apex callout timeouts and hits Marketing Cloud rate limits. The sync endpoint is designed for real-time use, not bulk.

**Solution:**

```apex
public class MCDataExtensionBulkSync {

    private static final String SUBDOMAIN = MC_Config__mdt.getInstance('Default').Subdomain__c;
    private static final String DE_EXTERNAL_KEY = 'AccountAudience_DE'; // matches DE ExternalKey in MC

    // Build and POST a chunk of rows to the async DE endpoint
    // Returns the requestId for polling
    public static String upsertRowsAsync(String accessToken, List<Map<String, Object>> rows) {
        Map<String, Object> payload = new Map<String, Object>{
            'items' => rows
        };

        HttpRequest req = new HttpRequest();
        req.setEndpoint(
            'https://' + SUBDOMAIN + '.rest.marketingcloudapis.com' +
            '/hub/v1/dataeventsasync/key:' + DE_EXTERNAL_KEY + '/rowset'
        );
        req.setMethod('POST');
        req.setHeader('Authorization', 'Bearer ' + accessToken);
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(payload));
        req.setTimeout(30000);

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() != 200) {
            throw new CalloutException('DE async upsert failed: ' + res.getBody());
        }

        Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        return (String) body.get('requestId');
    }

    // Poll for async job status — call after all chunks are submitted
    public static String checkAsyncStatus(String accessToken, String requestId) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(
            'https://' + SUBDOMAIN + '.rest.marketingcloudapis.com' +
            '/hub/v1/dataeventsasync/' + requestId
        );
        req.setMethod('GET');
        req.setHeader('Authorization', 'Bearer ' + accessToken);

        Http http = new Http();
        HttpResponse res = http.send(req);

        Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        return (String) body.get('status'); // 'Pending', 'Processing', 'Complete', 'Error'
    }
}
```

**Why it works:** The async endpoint (`dataeventsasync`) returns immediately with a `requestId`, decoupling submission from processing confirmation. This avoids Apex callout timeouts on large batches and stays within Marketing Cloud's rate limits. The polling pattern on `requestId` provides reliable status confirmation without blocking the Apex thread.

---

## Anti-Pattern: Using a Hardcoded Generic Marketing Cloud Endpoint URL

**What practitioners do:** Hardcode a URL like `https://www.exacttargetapis.com/interaction/v1/events` or use a non-tenant-specific base URL copied from old documentation or blog posts.

**What goes wrong:** The request either fails with a 401 (authentication mismatch) or a 404 because the endpoint does not route to the correct Marketing Cloud tenant. The error message is often cryptic ("invalid_client" or "endpoint not found") and does not clearly indicate the URL is wrong.

**Correct approach:** Always use the tenant-specific subdomain: `https://{{subdomain}}.rest.marketingcloudapis.com`. The subdomain is visible in Marketing Cloud Setup under the Installed Package → API Integration component. It is unique per Marketing Cloud account (Business Unit or parent MID).
