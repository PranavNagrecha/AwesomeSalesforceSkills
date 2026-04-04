# Examples — Flow External Services

## Example 1: Weather API Integration via HTTP Callout Action

**Context:** A service team's screen flow needs to display current weather conditions for a field service job site. The weather provider (e.g., OpenWeatherMap) exposes a simple GET endpoint but does not publish an OpenAPI spec in a Salesforce-compatible format.

**Problem:** Without a spec, External Services registration is impractical. The team wants a declarative solution that avoids Apex for this simple lookup.

**Solution:**

1. Create a Named Credential pointing to `https://api.openweathermap.org` using an External Credential with a custom header formula to inject the API key (`appid` query parameter can be added via a formula header or appended to the path).

2. In Flow Builder, add an **HTTP Callout** core action:
   - Named Credential: `OpenWeatherMap_NC`
   - Method: `GET`
   - Path: `/data/2.5/weather?q={!City_Input}&units=metric`
   - No request body needed.

3. Store outputs in variables:
   - `varResponseBody` (Text) — raw JSON string
   - `varStatusCode` (Number) — HTTP status

4. Add a **Decision** element: if `varStatusCode >= 400`, route to an error screen. Otherwise continue.

5. Use a **Transform** element to extract `main.temp` and `weather[0].description` from `varResponseBody` into `varTemperature` (Number) and `varWeatherDesc` (Text).

6. Display `varTemperature` and `varWeatherDesc` on a screen component.

7. Wire the HTTP Callout action's **fault connector** to a fault screen that shows "Unable to retrieve weather data. Please try again." and logs `$Flow.FaultMessage` to a custom log object.

```
HTTP Callout Configuration (Flow Builder):
  Named Credential: OpenWeatherMap_NC
  Method: GET
  Path: /data/2.5/weather?q={!Input_City}&units=metric
  Response_Body → varResponseBody (Text)
  Response_Status_Code → varStatusCode (Number)

Decision: varStatusCode >= 400 → Error Screen
Transform: varResponseBody.main.temp → varTemperature
           varResponseBody.weather[0].description → varWeatherDesc
```

**Why it works:** The HTTP Callout action handles the authentication via Named Credential without any Apex. The explicit status code check catches 4xx/5xx responses that the action's fault connector would not catch automatically. Transform handles flat JSON extraction declaratively.

---

## Example 2: Payment Gateway Verification via External Services Registration

**Context:** An order management screen flow must call a payment gateway's verification endpoint before marking an order as paid. The payment provider publishes a Swagger 2.0 (OpenAPI 2.0) spec. Multiple operations exist (verify payment, refund, void) and the team wants typed action parameters in Flow Builder.

**Problem:** Manually configuring each operation as a separate HTTP Callout action would be error-prone and hard to maintain as the API evolves. A typed, spec-driven approach is needed.

**Solution:**

1. Create a Named Credential (`PaymentGateway_NC`) pointing to `https://api.paymentprovider.com`. Configure OAuth 2.0 Client Credentials grant on the External Credential (server-to-server — the org calls the payment gateway with a service account, not per-user auth).

2. Navigate to **Setup > Integrations > External Services > Add an External Service**.
   - Service Name: `PaymentGateway`
   - Named Credential: `PaymentGateway_NC`
   - Upload or link the Swagger 2.0 spec JSON.
   - Salesforce validates the spec — review and dismiss any warnings about unsupported fields.

3. After registration, the `PaymentGateway` service appears in Flow Builder's Action palette with operations: `POST /payments/verify`, `POST /payments/refund`, etc.

4. In the order screen flow, add an **Action** element and select `PaymentGateway: POST /payments/verify`.
   - Map `orderId` (Text) → spec's `transaction_id` input.
   - Map `amount` (Currency) → spec's `amount` input.

5. Store outputs in variables typed to match the spec's response schema:
   - `varVerificationStatus` (Text) — maps to response `status` field
   - `varGatewayTransactionId` (Text) — maps to response `gateway_ref`

6. Add a **Decision**: if `varVerificationStatus == 'approved'`, update the order record. Otherwise route to a payment failure screen.

7. Wire the External Service action's **fault connector** to capture `$Flow.FaultMessage` in `varFaultDetail`, log to a `Payment_Error_Log__c` record, and display a user-safe message.

```
External Service Action Configuration:
  Service: PaymentGateway
  Operation: POST /payments/verify
  Inputs:
    transaction_id ← {!Order_Id}
    amount         ← {!Order_Amount}
  Outputs:
    status         → varVerificationStatus (Text)
    gateway_ref    → varGatewayTransactionId (Text)

Fault Path:
  Assign: varFaultDetail = {!$Flow.FaultMessage}
  Create Records: Payment_Error_Log__c (order_id, fault_detail, timestamp)
  Screen: "Payment verification could not be completed. Contact support."
```

**Why it works:** External Services generates typed action parameters from the spec, catching input mapping errors at build time rather than runtime. The fault connector handles network failures and server errors (non-2xx depending on spec config). Explicit Decision on `varVerificationStatus` handles business-level failures (e.g., `declined`) that are returned as valid HTTP 200 responses.

---

## Anti-Pattern: Hard-Coding the External API URL in Flow

**What practitioners do:** Add an HTTP Callout action and paste the full endpoint URL (including credentials as query parameters) directly into the Path field, bypassing the Named Credential.

**What goes wrong:** Flow Builder requires a Named Credential for the HTTP Callout action — a full URL is not accepted in the Path field (the Named Credential field is mandatory). Attempting to work around this by storing the URL in a Custom Setting and passing it to an Apex callout defeats the purpose of the declarative approach and introduces a security risk: credentials in Custom Settings are readable by any user with SOQL access or through the API.

**Correct approach:** Always create a Named Credential that holds the base URL and authentication. Reference it in the HTTP Callout action's Named Credential selector. Append only the resource path (e.g., `/v1/orders/{!orderId}`) in the Path field.
