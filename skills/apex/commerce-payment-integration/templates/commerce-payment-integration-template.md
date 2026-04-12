# Commerce Payment Integration — Work Template

Use this template when working on a custom CommercePayments Apex gateway adapter task.

## Scope

**Skill:** `commerce-payment-integration`

**Request summary:** (fill in what the practitioner asked for)

**Store type:** [ ] B2B Commerce (LWR)  [ ] D2C Commerce  [ ] Legacy Aura B2B (wrong skill — use admin/commerce-checkout-configuration)

**Integration path selected:**
- [ ] Salesforce Payments (Stripe native) — no custom Apex needed; stop here
- [ ] AppExchange payment package — identify package name: ___________________
- [ ] Custom CommercePayments Apex adapter — continue below

---

## Context Gathered

Answer these before writing any code:

- **Target gateway vendor and API version:** ___________________
- **API version of the org (must be v55.0+):** ___________________
- **Existing Named Credential for gateway (or name to create):** ___________________
- **RequestType branches required by this store's checkout flow:**
  - [ ] Tokenize
  - [ ] Authorization
  - [ ] PostAuthorization
  - [ ] Capture
  - [ ] ReferencedRefund
  - [ ] AuthorizationReversal
- **Digital wallet requirements:** [ ] Apple Pay (requires Salesforce Payments path)  [ ] None
- **SalesforceResultCodes mapping confirmed for each response type:** [ ] Yes

---

## PCI Isolation Verification

Before writing any Apex:

- [ ] Confirmed: raw card data (PAN, CVV, expiry) is NOT collected in any LWC input field that posts to Apex
- [ ] Confirmed: payment provider's cross-domain capture component (hosted iframe or redirect) is used for card data collection
- [ ] Confirmed: Apex adapter receives only an opaque token/nonce — never card numbers
- [ ] Confirmed: gateway API credentials are stored in Named Credential, not in Custom Settings or code

---

## Adapter Class Scaffold

**Apex class name:** ___________________

```apex
global class <ClassName> implements CommercePayments.PaymentGatewayAdapter {

    global CommercePayments.GatewayResponse processRequest(
            CommercePayments.PaymentGatewayContext context) {

        CommercePayments.RequestType reqType = context.getPaymentRequestType();

        if (reqType == CommercePayments.RequestType.Tokenize) {
            return handleTokenize(
                (CommercePayments.PaymentMethodTokenizationRequest)
                context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.Authorization) {
            return handleAuthorization(
                (CommercePayments.AuthorizationRequest)
                context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.PostAuthorization) {
            return handlePostAuthorization(
                (CommercePayments.PostAuthorizationRequest)
                context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.Capture) {
            return handleCapture(
                (CommercePayments.CaptureRequest)
                context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.ReferencedRefund) {
            return handleRefund(
                (CommercePayments.ReferencedRefundRequest)
                context.getPaymentRequest());
        } else if (reqType == CommercePayments.RequestType.AuthorizationReversal) {
            return handleReversal(
                (CommercePayments.AuthorizationReversalRequest)
                context.getPaymentRequest());
        }

        CommercePayments.GatewayErrorResponse err =
            new CommercePayments.GatewayErrorResponse();
        err.setGatewayMessage('Unhandled RequestType: ' + reqType);
        return err;
    }

    // Implement each handler method listed below.
    // Each handler must:
    //   1. Build HttpRequest using callout:<NamedCredentialName>/path
    //   2. Parse gateway JSON response
    //   3. Populate typed CommercePayments response object
    //   4. Call setSalesforceResultCodeInfo(...) — REQUIRED
    //   5. Return response (never throw)
}
```

---

## Named Credential

**Named Credential name:** ___________________
**Endpoint:** ___________________
**Authentication type:** [ ] Named Principal  [ ] Per-User Principal
**Protocol:** [ ] Password  [ ] OAuth  [ ] JWT  [ ] Custom Header

---

## Payment Gateway Provider Registration

- [ ] Payment Gateway Provider record created in Setup > Payment Gateway Providers
- [ ] Adapter class name entered in Provider record: ___________________
- [ ] Provider record linked to store in Payment Settings

---

## Test Class Checklist

- [ ] Test class created: `<ClassName>Test.cls`
- [ ] `HttpCalloutMock` implementations exist for each RequestType:
  - [ ] Tokenize mock
  - [ ] Authorization mock (success + decline)
  - [ ] PostAuthorization mock
  - [ ] Capture mock
  - [ ] ReferencedRefund mock
  - [ ] AuthorizationReversal mock
- [ ] Each test method calls `Test.setMock(HttpCalloutMock.class, ...)`
- [ ] All response objects asserted for non-null `getSalesforceResultCodeInfo()`
- [ ] Code coverage: ______% (target 90%+)

---

## Review Checklist

Copy from SKILL.md and tick as you complete them:

- [ ] Adapter implements all six RequestType branches
- [ ] No raw card data in any Apex code, test data, or Custom Settings
- [ ] All gateway credentials stored in Named Credentials
- [ ] Every handler returns a correctly typed CommercePayments response (no exceptions thrown)
- [ ] Test class achieves 90%+ coverage with mocked callouts
- [ ] Payment Gateway Provider metadata record created and linked to store
- [ ] End-to-end test order: tokenize → authorize → capture completed successfully

---

## Notes

Record any deviations from the standard pattern and why (e.g., gateway requires multi-step callout, partial PostAuthorization not needed, digital wallet handled separately):

___________________
