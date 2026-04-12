# LLM Anti-Patterns — AI Model Integration Apex

Common mistakes AI coding assistants make when generating or advising on AI model integration from Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating aiplatform.ModelsAPI as Authentication-Free and Skipping Platform Cache

**What the LLM generates:** Code that calls `new aiplatform.ModelsAPI().createChatGenerations(...)` directly without any caching layer, often with a comment like "no authentication needed — Einstein handles it automatically." The same pattern is then applied to legacy Einstein Vision or Language services without token management.

**Why it happens:** The External Services wrapper does hide the token exchange from the calling code, so surface-level analysis concludes no auth management is needed. Training data likely includes quick-start samples that omit caching for brevity.

**Correct pattern:**

```apex
// For aiplatform.ModelsAPI: auth is hidden but EACH call burns an Einstein Request entitlement.
// Cache model responses when inputs are stable.

// For legacy Einstein Vision/Language: ALWAYS use cache-aside token management.
String token = EinsteinTokenService.getToken(); // checks Cache.Org first
```

**Detection hint:** Look for `new aiplatform.ModelsAPI()` calls not wrapped in any caching layer in a high-frequency code path, or for direct token endpoint callouts without a preceding `Cache.Org.get(...)` check.

---

## Anti-Pattern 2: Synchronous Per-Record AI Callout Inside a Trigger

**What the LLM generates:** A trigger or trigger handler that calls `createChatGenerations` once per record in a `for (SObject record : Trigger.new)` loop, with no callout limit guard and no async deferral.

**Why it happens:** LLMs pattern-match on "call API per record in trigger" without understanding Apex governor limits. The pattern is common in REST integration examples that do not involve AI, and that context bleeds into AI callout generation.

**Correct pattern:**

```apex
// In trigger handler — do NOT call AI here
List<Id> ids = new List<Id>();
for (Account acc : Trigger.new) {
    ids.add(acc.Id);
}
// Defer to Queueable; never make callouts synchronously in bulk trigger context
if (!ids.isEmpty()) {
    System.enqueueJob(new AccountAiEnrichQueueable(ids));
}
```

**Detection hint:** Any `createChatGenerations` or `createGenerations` call inside a `for` loop that iterates over `Trigger.new` or `Trigger.newMap.values()`.

---

## Anti-Pattern 3: Direct Code200 Property Access Without Null-Check

**What the LLM generates:** Response traversal that immediately accesses `response.Code200.generations[0].message.content` or `response.Code200.generation.generatedText` without first checking `response.Code200 != null`.

**Why it happens:** LLMs copy the happy-path access pattern from documentation examples, which show the successful response path only. Error handling is rarely shown in getting-started documentation.

**Correct pattern:**

```apex
aiplatform.ModelsAPI.createChatGenerations_Response response =
    new aiplatform.ModelsAPI().createChatGenerations(MODEL_API_NAME, req);

// Always null-check Code200 before traversal
if (response.Code200 == null) {
    System.debug('Non-200 model response: ' + response);
    return null;
}

List<aiplatform.ModelsAPI_ChatGenerationItemOutput> generations =
    response.Code200.generations;
if (generations == null || generations.isEmpty()) {
    return null;
}

String content = generations[0].message.content;
```

**Detection hint:** Any direct property access on `response.Code200.` without a preceding `if (response.Code200 == null)` guard in the same method scope.

---

## Anti-Pattern 4: Hardcoding the Model API Name String Across Multiple Classes

**What the LLM generates:** Multiple Apex classes each defining a private static final constant like `private static final String MODEL = 'sfdc_ai__DefaultOpenAIGPT4OmniMini';` with the same literal string value repeated in each class.

**Why it happens:** LLMs follow the pattern of the first class generated and replicate it into subsequent classes. The configuration concern is treated as a constant rather than a managed value.

**Correct pattern:**

```apex
// Store in Custom Metadata Type: AI_Model_Config__mdt
// with fields: Model_Api_Name__c, Is_Active__c

AI_Model_Config__mdt config = [
    SELECT Model_Api_Name__c
    FROM AI_Model_Config__mdt
    WHERE DeveloperName = 'DefaultChatModel'
    LIMIT 1
];
String modelApiName = config.Model_Api_Name__c;
```

**Detection hint:** The literal string `sfdc_ai__Default` appearing in more than one Apex class file in the same project.

---

## Anti-Pattern 5: Using Batch Apex Scope Larger Than Callout Budget Allows for AI Processing

**What the LLM generates:** A Batch Apex class with `implements Database.Batchable<SObject>, Database.AllowsCallouts` and a default or large scope (200 records per execute). The execute method calls `createChatGenerations` once per record in the list.

**Why it happens:** LLMs know that adding `Database.AllowsCallouts` enables callouts in batch but do not calculate whether the scope size multiplied by callouts per record stays within the 100-callout limit. The interface declaration is treated as sufficient.

**Correct pattern:**

```apex
// When starting the batch, constrain scope to stay within callout budget
// 1 callout per record * scope 10 = 10 callouts per execute — well within 100
Database.executeBatch(new AccountAiEnrichBatch(), 10);

// In the Batch class execute method, process the bounded scope list
public void execute(Database.BatchableContext ctx, List<Account> scope) {
    // scope.size() <= 10; max 10 callouts in this execute call
    for (Account acc : scope) {
        String result = callModel(acc.Description);
        // persist result
    }
}
```

**Detection hint:** A Batch class implementing `Database.AllowsCallouts` with no explicit scope constraint at the call site (`Database.executeBatch(new MyBatch())`), combined with a per-record AI callout inside execute.

---

## Anti-Pattern 6: Logging or Storing JWT Bearer Tokens in Debug Logs or Custom Fields

**What the LLM generates:** Code that calls `System.debug('Token: ' + token)` or stores the Einstein JWT token in a custom field on a record for debugging purposes.

**Why it happens:** LLMs apply standard debugging patterns without recognizing that a JWT bearer token is a credential. Storing or logging bearer tokens is a security violation even when the token is short-lived.

**Correct pattern:**

```apex
// Never log the token value
// System.debug('Token: ' + token); // WRONG

// Log only that a token was obtained, not its value
System.debug('Einstein token retrieved from cache: ' + (token != null));

// Never store tokens in Salesforce fields — use Cache.Org with appropriate TTL
Cache.Org.put(CACHE_KEY, token, CACHE_TTL_SECONDS);
```

**Detection hint:** `System.debug` calls containing the variable holding the token, or DML inserting/updating a record with a field assigned the token string value.
