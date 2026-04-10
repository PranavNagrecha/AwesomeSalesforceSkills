# Examples — Commerce Checkout Configuration

## Example 1: Apex Payment Adapter for Stripe Authorization

**Context:** A B2B Commerce merchant on an LWR store uses Stripe as their payment gateway. Stripe Elements (client-side) tokenizes the card; the token is passed to Salesforce at checkout submission. The merchant needs an Apex adapter that authorizes the charge against Stripe's API.

**Problem:** Without a registered `sfdc_checkout.CartPaymentAuthorize` implementation, the payment step in CartCheckoutSession will not execute. The checkout hangs at the Payment Authorization state with a `CartValidationOutput` error indicating no payment adapter is configured.

**Solution:**

```apex
public class StripePaymentAdapter implements sfdc_checkout.CartPaymentAuthorize {

    private static final String STRIPE_CHARGE_ENDPOINT = 'callout:Stripe/v1/charges';

    public CartExtension.CartPaymentAuthorizationResponse authorizePayment(
        CartExtension.CartPaymentAuthorizationRequest request
    ) {
        CartExtension.CartPaymentAuthorizationResponse response =
            new CartExtension.CartPaymentAuthorizationResponse();

        String paymentToken = request.getPaymentToken();
        Decimal amount = request.getAmount();
        String currency = request.getCurrencyIsoCode().toLowerCase();

        HttpRequest req = new HttpRequest();
        req.setEndpoint(STRIPE_CHARGE_ENDPOINT);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/x-www-form-urlencoded');
        req.setBody(
            'amount=' + String.valueOf((amount * 100).intValue()) +
            '&currency=' + currency +
            '&source=' + paymentToken +
            '&capture=false'
        );

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> body =
                (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            String chargeId = (String) body.get('id');
            String stripeStatus = (String) body.get('status');

            if (stripeStatus == 'succeeded' || stripeStatus == 'requires_capture') {
                response.setAuthorized(true);
                response.setPaymentGatewayReferenceNumber(chargeId);
            } else {
                response.setAuthorized(false);
                response.setErrorMessage('Stripe returned status: ' + stripeStatus);
            }
        } else {
            // Always return setAuthorized(false) — never throw an exception
            response.setAuthorized(false);
            response.setErrorMessage('Gateway error: HTTP ' + res.getStatusCode());
        }

        return response;
    }
}
```

After deploying, register this class in **Commerce Setup > Payment > Payment Adapter Class**.

**Why it works:** The adapter returns a structured `CartPaymentAuthorizationResponse` in all code paths — including gateway errors and HTTP failures. This ensures CartCheckoutSession can transition cleanly to a declined or error state rather than entering the unrecoverable exception state. The Stripe charge is created as an authorization-only (`capture=false`) so the merchant can capture on shipment, consistent with B2B order-to-cash workflows.

---

## Example 2: Setting Billing Address on WebCart Before Order Creation

**Context:** A D2C store on LWR Managed Checkout is completing orders successfully, but the resulting OrderSummary records have a null `BillingAddress` field and no Contact linked on the Order. Finance reports downstream depend on billing address for invoice generation.

**Problem:** The checkout flow collects a shipping address but never copies it to the WebCart billing fields. At the moment CartCheckoutSession executes the order creation state, it reads `WebCart.BillingStreet` et al. to construct the billing contact — finding null values, it creates the Order with a null contact and does not error.

**Solution:**

In the LWR storefront's custom checkout summary component (an Extension Point or a wired LWC), add a step that writes billing fields to WebCart before the buyer submits:

```javascript
// checkoutSummaryController.js (LWC)
import { LightningElement, wire, api } from 'lwc';
import { updateRecord } from 'lightning/uiRecordApi';
import WEBCART_ID_FIELD from '@salesforce/schema/WebCart.Id';
import BILLING_STREET from '@salesforce/schema/WebCart.BillingStreet';
import BILLING_CITY from '@salesforce/schema/WebCart.BillingCity';
import BILLING_STATE from '@salesforce/schema/WebCart.BillingState';
import BILLING_POSTAL from '@salesforce/schema/WebCart.BillingPostalCode';
import BILLING_COUNTRY from '@salesforce/schema/WebCart.BillingCountry';

async setBillingFromShipping(cartId, shippingAddress) {
    const fields = {
        [WEBCART_ID_FIELD.fieldApiName]: cartId,
        [BILLING_STREET.fieldApiName]: shippingAddress.street,
        [BILLING_CITY.fieldApiName]: shippingAddress.city,
        [BILLING_STATE.fieldApiName]: shippingAddress.state,
        [BILLING_POSTAL.fieldApiName]: shippingAddress.postalCode,
        [BILLING_COUNTRY.fieldApiName]: shippingAddress.country,
    };
    await updateRecord({ fields });
}
```

Call `setBillingFromShipping` when the buyer confirms their address and checks "Same as shipping". For stores that collect a separate billing address, populate these fields from the billing address form instead.

**Why it works:** CartCheckoutSession reads billing fields from the WebCart record at the precise moment the order creation state executes. There is no mechanism for the platform to derive billing data after the fact. Writing these fields before submission is the only reliable path to a fully populated OrderSummary.

---

## Example 3: Guest Checkout Email and Phone Population

**Context:** A D2C headless storefront allows guest purchases. Buyers provide their email at cart creation time (for order confirmation emails) and a delivery address. After launch, support reports that all guest orders have a null Contact — order confirmation emails never fire.

**Problem:** For authenticated buyers, Salesforce populates Contact fields from the user profile. For guest buyers there is no profile. The shipping address captured by the storefront was never mapped to `CartDeliveryGroup.Email` and `CartDeliveryGroup.Phone`, so the platform had no source for these values when constructing the Order Contact.

**Solution:**

When the guest submits their shipping address, POST to the Commerce Checkout API to update the delivery group with email and phone alongside the address:

```json
PATCH /commerce/webstores/{webstoreId}/checkouts/{checkoutId}

{
  "deliveryAddress": {
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "postalCode": "94105",
    "country": "US",
    "email": "buyer@example.com",
    "phone": "4155551234",
    "firstName": "Jane",
    "lastName": "Doe"
  }
}
```

For Aura Flow Builder stores, the `Get Delivery Address` and `Update Delivery Address` Flow elements expose `Email` and `Phone` as input fields. Map the form values to these fields in the Flow before calling the Cart Calculate API.

**Why it works:** `CartDeliveryGroup` stores `Email` and `Phone` as first-class fields. When CartCheckoutSession creates the Order, it reads these fields to construct the Contact record. Populating them at address-entry time — rather than assuming the platform will derive them — guarantees a non-null Contact on every guest order.

---

## Anti-Pattern: Throwing an Exception from the Payment Adapter on Gateway Failure

**What practitioners do:** In the Apex Payment Adapter, they write a standard try/catch that re-throws or lets unhandled exceptions propagate when the gateway returns a non-2xx HTTP status.

**What goes wrong:** An unhandled exception from inside the `authorizePayment` method leaves the `CartCheckoutSession` in an error state from which it cannot recover. The buyer sees a generic error page. The session cannot be retried — it must be deleted via the Commerce Checkout API and a fresh checkout started, losing all progress. This is especially destructive in B2B where carts may carry dozens of line items.

**Correct approach:** Always return a `CartPaymentAuthorizationResponse` with `setAuthorized(false)` and an `errorMessage` when the gateway fails. Reserve exception throwing for truly unexpected platform-level failures (e.g., null pointer on a required field that the platform should have guaranteed). Handle all gateway response codes — including timeouts — with a structured declined response.
