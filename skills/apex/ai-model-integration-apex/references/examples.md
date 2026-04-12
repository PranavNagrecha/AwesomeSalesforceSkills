# Examples — AI Model Integration Apex

## Example 1: Chat Generation with aiplatform.ModelsAPI and Null-Safe Response Parsing

**Context:** A service class needs to call an LLM to classify a support case description. The org has Einstein AI enabled and the External Services wrapper for `aiplatform.ModelsAPI` is available.

**Problem:** Without null-safe response traversal, a non-200 response from the model — quota exceeded, model error, or throttle — causes a NullPointerException at the `Code200.generation.generatedText` path. The error surfaces as a confusing NPE rather than a meaningful model failure.

**Solution:**

```apex
public class CaseClassifierService {

    private static final String MODEL_API_NAME = 'sfdc_ai__DefaultOpenAIGPT4OmniMini';

    public static String classifyCase(String caseDescription) {
        aiplatform.ModelsAPI.createChatGenerations_Request req =
            new aiplatform.ModelsAPI.createChatGenerations_Request();

        aiplatform.ModelsAPI_ChatGenerationsRequest body =
            new aiplatform.ModelsAPI_ChatGenerationsRequest();

        aiplatform.ModelsAPI_ChatMessage systemMsg =
            new aiplatform.ModelsAPI_ChatMessage();
        systemMsg.role = 'system';
        systemMsg.content = 'Classify the support case into one of: Billing, Technical, Account, Other.';

        aiplatform.ModelsAPI_ChatMessage userMsg =
            new aiplatform.ModelsAPI_ChatMessage();
        userMsg.role = 'user';
        userMsg.content = caseDescription;

        body.messages = new List<aiplatform.ModelsAPI_ChatMessage>{ systemMsg, userMsg };
        req.body = body;

        try {
            aiplatform.ModelsAPI.createChatGenerations_Response response =
                new aiplatform.ModelsAPI().createChatGenerations(MODEL_API_NAME, req);

            if (response.Code200 == null) {
                // Model returned a non-200 status — log and return a safe default
                System.debug('AI model non-200 response: ' + response);
                return 'Other';
            }

            List<aiplatform.ModelsAPI_ChatGenerationItemOutput> generations =
                response.Code200.generations;

            if (generations == null || generations.isEmpty()) {
                return 'Other';
            }

            return generations[0].message.content;

        } catch (aiplatform.ModelsAPI.createChatGenerationsException ex) {
            System.debug('ModelsAPI exception: ' + ex.getMessage());
            return 'Other';
        }
    }
}
```

**Why it works:** The null-check on `response.Code200` catches all non-200 model responses before traversal. The typed exception `createChatGenerationsException` separates model API errors from generic Apex exceptions, allowing distinct handling.

---

## Example 2: Legacy Einstein Platform Services with Platform Cache Token Management

**Context:** An org uses Einstein Vision to classify images attached to Work Orders. The image classification endpoint requires a Bearer JWT token obtained from the Einstein API token endpoint.

**Problem:** Without Platform Cache, every Work Order update fetches a fresh JWT token before making the image classification callout. Under moderate load (20 Work Orders updated simultaneously) this results in 40 callouts per transaction — 20 for token fetches and 20 for image calls — instead of 20, burning double the Einstein Request entitlement budget.

**Solution:**

```apex
public class EinsteinTokenService {

    private static final String CACHE_KEY = 'local.EinsteinToken.jwt';
    private static final String TOKEN_ENDPOINT =
        'https://api.einstein.ai/v2/oauth2/token';
    // TTL 30 seconds less than actual 60-minute token expiry
    private static final Integer CACHE_TTL_SECONDS = 3570;

    public static String getToken() {
        String cached = (String) Cache.Org.get(CACHE_KEY);
        if (String.isNotBlank(cached)) {
            return cached;
        }
        return fetchAndCacheToken();
    }

    private static String fetchAndCacheToken() {
        // Named Credential handles the private key; callout produces the JWT
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Einstein_Token_NC');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/x-www-form-urlencoded');
        req.setBody('grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer'
            + '&assertion=' + buildJwtAssertion());

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() != 200) {
            throw new EinsteinTokenException('Token fetch failed: ' + res.getStatus());
        }

        Map<String, Object> parsed =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        String token = (String) parsed.get('access_token');

        Cache.Org.put(CACHE_KEY, token, CACHE_TTL_SECONDS);
        return token;
    }

    private static String buildJwtAssertion() {
        // Build and sign JWT — implementation uses Crypto class
        // and a Connected App private key stored in a Custom Setting or Named Credential
        // (implementation detail omitted for brevity)
        return '';
    }

    public class EinsteinTokenException extends Exception {}
}


public class EinsteinVisionService {

    public static String classifyImage(String imageUrl) {
        String token = EinsteinTokenService.getToken();

        HttpRequest req = new HttpRequest();
        req.setEndpoint('https://api.einstein.ai/v2/vision/predict');
        req.setMethod('POST');
        req.setHeader('Authorization', 'Bearer ' + token);
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{
            'modelId' => 'GeneralImageClassifier',
            'sampleLocation' => imageUrl
        }));

        Http http = new Http();
        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() != 200) {
            throw new EinsteinVisionException('Vision API error: ' + res.getStatus());
        }

        Map<String, Object> body =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        List<Object> probabilities = (List<Object>) body.get('probabilities');
        Map<String, Object> top = (Map<String, Object>) probabilities[0];
        return (String) top.get('label');
    }

    public class EinsteinVisionException extends Exception {}
}
```

**Why it works:** `EinsteinTokenService.getToken()` reads from `Cache.Org` first. Only on a miss (cold start or expiry) does it make the token callout. The TTL is 3570 seconds (59.5 minutes), 30 seconds below the actual 60-minute token expiry, ensuring the cache never serves an expired token. All callers share one cached token, reducing callout count to one AI callout per record rather than two.

---

## Example 3: Queueable Chain for Bulk AI Processing

**Context:** A nightly automation needs to enrich 500 Account records with AI-generated summaries using `aiplatform.ModelsAPI`. Running this synchronously in a batch execute method with a scope of 500 would exceed the 100-callout limit.

**Problem:** Calling `createChatGenerations` once per record in a single transaction hits the callout limit at record 101 and throws `System.LimitException`, leaving remaining records unprocessed.

**Solution:**

```apex
public class AccountAiEnrichQueueable implements Queueable, Database.AllowsCallouts {

    private static final Integer SLICE_SIZE = 10;
    private static final String MODEL_API_NAME = 'sfdc_ai__DefaultOpenAIGPT4OmniMini';

    private List<Id> remainingIds;

    public AccountAiEnrichQueueable(List<Id> remainingIds) {
        this.remainingIds = remainingIds;
    }

    public void execute(QueueableContext ctx) {
        if (remainingIds == null || remainingIds.isEmpty()) {
            return; // Termination guard — nothing left to process
        }

        List<Id> currentSlice = new List<Id>();
        List<Id> nextBatch = new List<Id>();

        for (Integer i = 0; i < remainingIds.size(); i++) {
            if (i < SLICE_SIZE) {
                currentSlice.add(remainingIds[i]);
            } else {
                nextBatch.add(remainingIds[i]);
            }
        }

        List<Account> accounts = [
            SELECT Id, Name, Description
            FROM Account
            WHERE Id IN :currentSlice
        ];

        List<Account> toUpdate = new List<Account>();

        for (Account acc : accounts) {
            String summary = callModel(acc.Description);
            if (summary != null) {
                toUpdate.add(new Account(Id = acc.Id, AI_Summary__c = summary));
            }
        }

        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }

        // Re-enqueue for remaining records
        if (!nextBatch.isEmpty()) {
            System.enqueueJob(new AccountAiEnrichQueueable(nextBatch));
        }
    }

    private String callModel(String description) {
        if (String.isBlank(description)) {
            return null;
        }

        aiplatform.ModelsAPI.createChatGenerations_Request req =
            new aiplatform.ModelsAPI.createChatGenerations_Request();

        aiplatform.ModelsAPI_ChatGenerationsRequest body =
            new aiplatform.ModelsAPI_ChatGenerationsRequest();

        aiplatform.ModelsAPI_ChatMessage msg = new aiplatform.ModelsAPI_ChatMessage();
        msg.role = 'user';
        msg.content = 'Summarize this account description in one sentence: ' + description;

        body.messages = new List<aiplatform.ModelsAPI_ChatMessage>{ msg };
        req.body = body;

        try {
            aiplatform.ModelsAPI.createChatGenerations_Response response =
                new aiplatform.ModelsAPI().createChatGenerations(MODEL_API_NAME, req);

            if (response.Code200 == null
                    || response.Code200.generations == null
                    || response.Code200.generations.isEmpty()) {
                return null;
            }

            return response.Code200.generations[0].message.content;

        } catch (Exception ex) {
            System.debug('AI callout failed for record: ' + ex.getMessage());
            return null;
        }
    }
}
```

**Why it works:** Each Queueable execution processes exactly `SLICE_SIZE` (10) records, making 10 callouts — well within the 100-callout limit. The termination guard `if (remainingIds.isEmpty()) return;` ensures the chain stops cleanly. Re-enqueue only fires when records remain, preventing infinite loops. `Database.AllowsCallouts` is required for callouts inside Queueable.
