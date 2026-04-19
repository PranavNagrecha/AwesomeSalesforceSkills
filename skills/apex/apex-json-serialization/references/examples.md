# Examples — Apex JSON Serialization

## Example 1: Outbound REST callout with null field suppression

**Context:** An integration sends order data to a third-party REST API. The API uses strict JSON schema validation and rejects payloads containing null fields for optional attributes.

**Problem:** `JSON.serialize(order)` includes all null fields (e.g., `"couponCode": null`, `"giftMessage": null`), causing the external API to return a 400 Bad Request.

**Solution:**

```apex
public class OrderPayload {
    public String orderId;
    public Decimal totalAmount;
    public String couponCode;   // optional — may be null
    public String giftMessage;  // optional — may be null
    public List<LineItem> lineItems;
}

public class LineItem {
    public String sku;
    public Integer quantity;
    public String note; // optional
}

// Build payload
OrderPayload payload = new OrderPayload();
payload.orderId = order.OrderNumber;
payload.totalAmount = order.TotalAmount;
payload.lineItems = buildLineItems(order);
// couponCode and giftMessage stay null

// Serialize with null suppression
HttpRequest req = new HttpRequest();
req.setBody(JSON.serialize(payload, true)); // suppresses nulls recursively
req.setMethod('POST');
req.setEndpoint('callout:OrderAPI/orders');
```

**Why it works:** The second `true` argument to `JSON.serialize` omits any field (at any nesting level) whose value is null. The resulting payload is `{"orderId":"...","totalAmount":...,"lineItems":[...]}` with no null entries.

---

## Example 2: Deserializing a heterogeneous API response with type safety

**Context:** A webhook handler receives JSON payloads from an external system. The payload shape is documented but varies by event type — some fields may be missing or have different types across event versions.

**Problem:** Using `JSON.deserialize` directly without error handling throws uncaught `TypeException` when the payload has an unexpected type on a field, crashing the entire transaction.

**Solution:**

```apex
public class WebhookPayload {
    public String eventType;
    public String resourceId;
    public Map<String, Object> metadata; // untyped for flexible inner shape
}

@RestResource(urlMapping='/webhook/*')
global class WebhookHandler {
    @HttpPost
    global static void handleEvent() {
        RestRequest req = RestContext.request;
        String body = req.requestBody.toString();
        WebhookPayload payload;
        try {
            payload = (WebhookPayload) JSON.deserialize(body, WebhookPayload.class);
        } catch (JSONException e) {
            RestContext.response.statusCode = 400;
            RestContext.response.responseBody = Blob.valueOf('{"error":"malformed JSON"}');
            return;
        } catch (System.TypeException e) {
            // Log the raw body for debugging
            System.debug(LoggingLevel.ERROR, 'TypeException parsing webhook: ' + body);
            RestContext.response.statusCode = 422;
            RestContext.response.responseBody = Blob.valueOf('{"error":"schema mismatch"}');
            return;
        }
        processEvent(payload);
    }
}
```

**Why it works:** Catching both `JSONException` (malformed JSON) and `TypeException` (valid JSON but wrong shape) handles the two distinct failure modes. Using `Map<String, Object>` for the `metadata` field avoids TypeException on flexible inner structures while keeping the outer fields typed.

---

## Anti-Pattern: Using `JSON.deserialize` without catching TypeException

**What practitioners do:** Call `JSON.deserialize(response, MyClass.class)` directly in a callout handler without error handling, assuming that extra or missing fields are tolerated.

**What goes wrong:** When the external API changes a field type (e.g., changes `amount` from a Number to a String in an error response), `TypeException` propagates uncaught, rolls back the entire transaction, and may cause duplicate processing if the caller retries.

**Correct approach:** Always wrap `JSON.deserialize` on external data in try/catch blocks for both `JSONException` and `System.TypeException`. For truly dynamic shapes, use `JSON.deserializeUntyped` and navigate the `Map<String,Object>` tree manually.
