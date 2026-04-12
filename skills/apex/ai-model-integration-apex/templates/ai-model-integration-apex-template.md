# AI Model Integration Apex — Work Template

Use this template when implementing or reviewing AI model callouts from Apex.

## Scope

**Skill:** `ai-model-integration-apex`

**Request summary:** (fill in what the user asked for — e.g. "Add AI-generated case summary on Case insert" or "Classify images attached to Work Orders using Einstein Vision")

## Context Gathered

Answer these before writing any code:

- **API surface:** aiplatform.ModelsAPI / Legacy Einstein Vision / Legacy Einstein Language / Direct HTTP to external LLM
- **Model API name (if ModelsAPI):** e.g. `sfdc_ai__DefaultOpenAIGPT4OmniMini`
- **Transaction volume:** Single-record synchronous / Bulk trigger / Batch / Scheduled
- **Platform Cache partition available:** Yes / No — partition name:
- **Einstein Request entitlement limit:** (check Einstein Usage in Setup)
- **Callout budget for this transaction context:** (100 max per transaction)
- **Is AI result required before the record is committed?** Yes (sync required) / No (async acceptable)

## API Call Pattern Selected

Choose one:

- [ ] `aiplatform.ModelsAPI.createChatGenerations` — chat-style prompt with message history
- [ ] `aiplatform.ModelsAPI.createGenerations` — completion-style text generation
- [ ] `aiplatform.ModelsAPI.createEmbeddings` — vector embedding generation
- [ ] Legacy Einstein Vision — `https://api.einstein.ai/v2/vision/predict`
- [ ] Legacy Einstein Language — `https://api.einstein.ai/v2/language/...`

## Implementation Checklist

### API Call
- [ ] Model API name sourced from Custom Metadata or Custom Setting (not hardcoded)
- [ ] Request body constructed with correct typed request class
- [ ] Callout wrapped in try-catch for typed API exception (`createChatGenerationsException` etc.)
- [ ] `response.Code200` null-checked before accessing any nested property
- [ ] Non-200 response logged with enough context to diagnose the failure

### Token Management (Legacy Einstein only)
- [ ] Token acquisition wrapped in cache-aside check: `Cache.Org.get(CACHE_KEY)`
- [ ] Cache TTL set to 30–60 seconds less than actual token validity
- [ ] Token never logged via `System.debug` or stored in a Salesforce field
- [ ] Token endpoint URL in Named Credential (not hardcoded)

### Governor Limit Safety
- [ ] Callout count per transaction estimated for expected batch size
- [ ] Synchronous paths constrained to cases where AI result is required before commit
- [ ] Bulk processing refactored to Queueable with `Database.AllowsCallouts`
- [ ] Queueable slice size defined so callouts per execution stay under 100
- [ ] Queueable termination guard in place (`if (remainingIds.isEmpty()) return;`)

### Reliability
- [ ] Graceful default or failure signal returned when model response is unavailable
- [ ] Per-record AI failures do not fail the entire batch (Queueable or Batch design)
- [ ] Retryable failure state recorded if re-processing is needed

## Code Scaffold

```apex
// aiplatform.ModelsAPI — Chat Generation (replace TODO placeholders)
public class TODO_AiServiceClass {

    private static final String MODEL_API_NAME =
        AI_Model_Config__mdt.getInstance('DefaultChatModel').Model_Api_Name__c;

    public static String generate(String userPrompt) {
        aiplatform.ModelsAPI.createChatGenerations_Request req =
            new aiplatform.ModelsAPI.createChatGenerations_Request();

        aiplatform.ModelsAPI_ChatGenerationsRequest body =
            new aiplatform.ModelsAPI_ChatGenerationsRequest();

        aiplatform.ModelsAPI_ChatMessage msg = new aiplatform.ModelsAPI_ChatMessage();
        msg.role = 'user';
        msg.content = userPrompt;

        body.messages = new List<aiplatform.ModelsAPI_ChatMessage>{ msg };
        req.body = body;

        try {
            aiplatform.ModelsAPI.createChatGenerations_Response response =
                new aiplatform.ModelsAPI().createChatGenerations(MODEL_API_NAME, req);

            if (response.Code200 == null
                    || response.Code200.generations == null
                    || response.Code200.generations.isEmpty()) {
                System.debug('AI model non-success response: ' + response);
                return null;
            }

            return response.Code200.generations[0].message.content;

        } catch (aiplatform.ModelsAPI.createChatGenerationsException ex) {
            System.debug('ModelsAPI exception: ' + ex.getMessage());
            return null;
        }
    }
}
```

## Notes

Record any deviations from the standard pattern and why they were chosen.

- Deviation:
- Reason:
