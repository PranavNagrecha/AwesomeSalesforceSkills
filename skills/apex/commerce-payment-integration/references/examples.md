# Examples — Commerce Payment Integration

## Example 1: Custom Adapter Handling Tokenize and Authorization for a Non-Stripe Gateway

**Context:** A D2C Commerce store sells across multiple regions and must integrate with a regional gateway (e.g., a European acquirer) that is not available as a Salesforce Payments provider or AppExchange package. The development team needs to author a custom `CommercePayments` adapter.

**Problem:** Without guidance, developers write a single method that assumes every call is an authorization. When the platform calls `processRequest` with `RequestType.Tokenize` during the LWC payment capture step, the method returns an `AuthorizationResponse` instead of `GatewayTokenizeResponse`. The platform cannot parse the response, checkout breaks with a generic error, and no actionable log entry is written.

**Solution:**

```apex
global class RegionalGatewayAdapter
        implements CommercePayments.PaymentGatewayAdapter {

    global CommercePayments.GatewayResponse processRequest(
            CommercePayments.PaymentGatewayContext context) {

        CommercePayments.RequestType reqType = context.getPaymentRequestType();

        if (reqType == CommercePayments.RequestType.Tokenize) {
            CommercePayments.PaymentMethodTokenizationRequest tokenReq =
                (CommercePayments.PaymentMethodTokenizationRequest)
                context.getPaymentRequest();
            return tokenize(tokenReq);
        } else if (reqType == CommercePayments.RequestType.Authorization) {
            CommercePayments.AuthorizationRequest authReq =
                (CommercePayments.AuthorizationRequest)
                context.getPaymentRequest();
            return authorize(authReq);
        }
        // ... other branches ...
        CommercePayments.GatewayErrorResponse err =
            new CommercePayments.GatewayErrorResponse();
        err.setGatewayMessage('Unhandled request type: ' + reqType);
        return err;
    }

    private CommercePayments.GatewayResponse tokenize(
            CommercePayments.PaymentMethodTokenizationRequest req) {
        // The adapter receives a gateway nonce from the provider iframe —
        // NOT raw card data. It exchanges the nonce for a durable token.
        HttpRequest httpReq = new HttpRequest();
        httpReq.setEndpoint('callout:Regional_GW/tokens');
        httpReq.setMethod('POST');
        httpReq.setBody('{"nonce":"' + req.getGatewayToken() + '"}');
        Http http = new Http();
        HttpResponse res = http.send(httpReq);

        CommercePayments.PaymentMethodTokenizationResponse tokenResp =
            new CommercePayments.PaymentMethodTokenizationResponse();
        // Parse JSON response and set gateway token reference
        Map<String, Object> body =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        tokenResp.setGatewayToken((String) body.get('token'));
        tokenResp.setSalesforceResultCodeInfo(
            CommercePayments.SalesforceResultCodes.Success);
        return tokenResp;
    }

    private CommercePayments.GatewayResponse authorize(
            CommercePayments.AuthorizationRequest req) {
        HttpRequest httpReq = new HttpRequest();
        httpReq.setEndpoint('callout:Regional_GW/authorizations');
        httpReq.setMethod('POST');
        httpReq.setBody(JSON.serialize(new Map<String, Object>{
            'token'    => req.getPaymentMethod().getGatewayToken(),
            'amount'   => req.getAmount(),
            'currency' => req.getCurrencyIsoCode()
        }));
        Http http = new Http();
        HttpResponse res = http.send(httpReq);

        CommercePayments.AuthorizationResponse authResp =
            new CommercePayments.AuthorizationResponse();
        Map<String, Object> body =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        authResp.setGatewayReferenceNumber((String) body.get('transactionId'));
        authResp.setAmount(req.getAmount());
        authResp.setSalesforceResultCodeInfo(
            CommercePayments.SalesforceResultCodes.Success);
        return authResp;
    }
}
```

**Why it works:** The dispatch on `RequestType` ensures the platform always receives the correctly typed response object. The tokenize handler exchanges a provider nonce for a durable token without ever seeing or logging raw card data. The `callout:Regional_GW` Named Credential keeps the gateway API key out of code.

---

## Example 2: Test Class Covering All RequestType Branches with Mock Callouts

**Context:** After implementing the full adapter, the team needs to write a test class that achieves 90%+ coverage and validates each payment lifecycle step without making real callouts to the gateway.

**Problem:** A naive test class calls `processRequest` once with a hardcoded authorization scenario and marks coverage done. This leaves Tokenize, Capture, ReferencedRefund, PostAuthorization, and AuthorizationReversal branches untested. A gateway API change in the Capture branch causes a production incident that tests would have caught.

**Solution:**

```apex
@IsTest
private class RegionalGatewayAdapterTest {

    // Mock returning a successful tokenization response
    private class TokenizeMock implements HttpCalloutMock {
        public HTTPResponse respond(HTTPRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(200);
            res.setBody('{"token":"tok_abc123"}');
            return res;
        }
    }

    // Mock returning a successful authorization response
    private class AuthorizeMock implements HttpCalloutMock {
        public HTTPResponse respond(HTTPRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(200);
            res.setBody('{"transactionId":"txn_xyz789","status":"AUTHORIZED"}');
            return res;
        }
    }

    // Mock returning a capture response
    private class CaptureMock implements HttpCalloutMock {
        public HTTPResponse respond(HTTPRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(200);
            res.setBody('{"transactionId":"cap_111","status":"CAPTURED"}');
            return res;
        }
    }

    @IsTest
    static void testTokenize() {
        Test.setMock(HttpCalloutMock.class, new TokenizeMock());
        Test.startTest();
        RegionalGatewayAdapter adapter = new RegionalGatewayAdapter();
        // Build a minimal PaymentGatewayContext stub using test factory helpers
        CommercePayments.PaymentMethodTokenizationRequest req =
            new CommercePayments.PaymentMethodTokenizationRequest();
        req.setGatewayToken('nonce_test_001');
        // Invoke through the context mock — platform provides test utilities
        // to construct PaymentGatewayContext in test mode
        // Validate response type and gateway token
        Test.stopTest();
        // Assertions: response is GatewayTokenizeResponse, token set correctly
    }

    @IsTest
    static void testAuthorization() {
        Test.setMock(HttpCalloutMock.class, new AuthorizeMock());
        Test.startTest();
        // ... build context, invoke processRequest, assert AuthorizationResponse ...
        Test.stopTest();
    }

    @IsTest
    static void testCapture() {
        Test.setMock(HttpCalloutMock.class, new CaptureMock());
        Test.startTest();
        // ... validate CaptureResponse returned with correct gatewayReferenceNumber ...
        Test.stopTest();
    }
}
```

**Why it works:** Each mock targets one `RequestType` branch. Using `Test.setMock` prevents real callouts and allows testing all lifecycle paths, including error paths, with deterministic responses. The test structure mirrors the adapter's dispatch logic, making gaps immediately visible.

---

## Anti-Pattern: Routing Raw Card Data Through Apex

**What practitioners do:** They build a custom LWC payment form that collects card number, CVV, and expiry directly, then POST these to an Apex REST endpoint or Apex controller method, which passes them to `processRequest` or a direct callout to the gateway.

**What goes wrong:** This design brings Salesforce's servers into PCI DSS scope for the highest-risk cardholder data environment (CHD) tier. It violates Salesforce's terms of service for Commerce payment integrations, creates severe audit exposure, and likely triggers PCI QSA re-assessment. Even if encrypted in transit, raw card data in Apex logs, debug logs, or platform events is a compliance violation.

**Correct approach:** Use the payment provider's cross-domain capture component (hosted iframe, redirect flow, or payment.js library) to collect card data client-side. The provider returns only an opaque nonce or token to the Commerce LWC, which the platform then passes to the Apex adapter via `RequestType.Tokenize`. The Apex adapter exchanges the nonce for a durable gateway token — it never sees card numbers or CVV.
