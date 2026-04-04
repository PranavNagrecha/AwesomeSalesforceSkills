# Examples — Continuation Callouts

## Example 1: Visualforce Quote Generation with 60-Second Timeout

**Context:** An insurance quoting Visualforce page calls an external rating engine that consistently takes 25–50 seconds to compute a premium. The synchronous callout limit (10 seconds) causes `System.CalloutException: Read timed out` before the service ever responds.

**Problem:** Using `Http.send()` directly in the VF controller action blocks the Salesforce request thread and hits the 10-second timeout hard ceiling before the rating engine responds.

**Solution:**

```apex
public class InsuranceQuoteController {

    public String policyId   { get; set; }
    public String premiumResult { get; set; }
    public Boolean hasError  { get; set; }

    // Phase 1: Build and hand off the callout to the Continuation framework
    public Continuation startPremiumCalculation() {
        hasError = false;

        // Set timeout to 60 seconds — enough for the rating engine
        Continuation con = new Continuation(60);
        con.continuationMethod = 'processPremiumResponse';

        HttpRequest req = new HttpRequest();
        req.setMethod('POST');
        // Named Credential encapsulates auth; must also be in Remote Site Settings
        req.setEndpoint('callout:RatingEngine/api/v2/premium');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, String>{
            'policyId' => policyId,
            'product'  => 'AUTO'
        }));

        con.addHttpRequest(req);

        // Pass only the policyId — simple scalar, always serializable
        con.state = policyId;

        return con; // Platform fires the HTTP request; thread is freed
    }

    // Phase 2: Called by the platform after the HTTP response arrives
    public Object processPremiumResponse(List<String> labels, Object state) {
        String savedPolicyId = (String) state;
        HttpResponse res = Continuation.getResponse(labels[0]);

        if (res.getStatusCode() == 200) {
            Map<String, Object> body =
                (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            premiumResult = 'Policy ' + savedPolicyId +
                            ' — Premium: $' + body.get('annualPremium');
        } else {
            hasError     = true;
            premiumResult = 'Rating engine returned HTTP ' + res.getStatusCode();
        }

        return null; // null = re-render same page; PageReference = navigate
    }
}
```

**Visualforce page:**
```xml
<apex:page controller="InsuranceQuoteController">
    <apex:form>
        <apex:inputText value="{!policyId}" label="Policy ID"/>
        <apex:commandButton value="Calculate Premium"
                            action="{!startPremiumCalculation}"
                            reRender="quotePanel"/>
        <apex:outputPanel id="quotePanel">
            <apex:outputText value="{!premiumResult}" rendered="{!!hasError}"/>
            <apex:outputText value="{!premiumResult}" styleClass="errorText"
                             rendered="{!hasError}"/>
        </apex:outputPanel>
    </apex:form>
</apex:page>
```

**Test class pattern:**
```apex
@IsTest
static void testPremiumCalculation() {
    InsuranceQuoteController ctrl = new InsuranceQuoteController();
    ctrl.policyId = 'POL-001';

    // Phase 1: get the Continuation object
    Continuation con = (Continuation) ctrl.startPremiumCalculation();
    System.assertNotEquals(null, con);

    // Inject mock response
    HttpResponse mockRes = new HttpResponse();
    mockRes.setStatusCode(200);
    mockRes.setBody('{"annualPremium": 1200.00}');
    String label = con.requests.keySet().iterator().next();
    Test.setContinuationResponse(label, mockRes);

    // Phase 2: invoke callback
    Object result = Test.invokeContinuationMethod(ctrl, con);
    System.assertEquals(null, result);
    System.assert(ctrl.premiumResult.contains('1200'));
}
```

**Why it works:** The `Continuation` object signals the platform to proxy the HTTP request externally. The Salesforce request thread is freed immediately after Phase 1 returns, preventing any timeout. The callback fires in a new transaction context with fresh governor limits.

---

## Example 2: Parallel Inventory and Pricing Aggregation from LWC

**Context:** A Lightning Web Component on a product detail page needs current stock levels from an ERP system and live pricing from a pricing microservice. Both calls are independent but each averages 15–20 seconds. Sequential calls would take 30–40 seconds total.

**Problem:** Firing them one after the other either times out (synchronous) or requires two separate user actions. An LWC using standard `@AuraEnabled` methods with `Http.send()` hits the 10-second synchronous limit.

**Solution:**

```apex
// ProductDetailController.cls
public with sharing class ProductDetailController {

    @AuraEnabled(continuation=true)
    public static Object startProductLoad(String productSku) {
        Continuation con = new Continuation(45);
        con.continuationMethod = 'processProductData';

        // Request 1 — ERP inventory
        HttpRequest erpReq = new HttpRequest();
        erpReq.setMethod('GET');
        erpReq.setEndpoint('callout:ERPService/inventory/' +
                           EncodingUtil.urlEncode(productSku, 'UTF-8'));
        String erpLabel = con.addHttpRequest(erpReq);

        // Request 2 — Pricing microservice
        HttpRequest priceReq = new HttpRequest();
        priceReq.setMethod('GET');
        priceReq.setEndpoint('callout:PricingService/sku/' +
                             EncodingUtil.urlEncode(productSku, 'UTF-8'));
        String priceLabel = con.addHttpRequest(priceReq);

        // State: map of labels so callback can retrieve by semantic name
        con.state = new Map<String, String>{
            'sku'   => productSku,
            'erp'   => erpLabel,
            'price' => priceLabel
        };

        return con;
    }

    @AuraEnabled(continuation=true)
    public static Object processProductData(List<String> labels, Object state) {
        Map<String, String> ctx = (Map<String, String>) state;

        HttpResponse erpRes   = Continuation.getResponse(ctx.get('erp'));
        HttpResponse priceRes = Continuation.getResponse(ctx.get('price'));

        Map<String, Object> result = new Map<String, Object>();

        if (erpRes.getStatusCode() == 200) {
            result.put('inventory', JSON.deserializeUntyped(erpRes.getBody()));
        } else {
            result.put('inventoryError', erpRes.getStatusCode());
        }

        if (priceRes.getStatusCode() == 200) {
            result.put('pricing', JSON.deserializeUntyped(priceRes.getBody()));
        } else {
            result.put('pricingError', priceRes.getStatusCode());
        }

        return JSON.serialize(result);
    }
}
```

```javascript
// productDetail.js
import { LightningElement, api } from 'lwc';
import { invokeAction }          from 'lightning/actions';
import startProductLoad          from '@salesforce/apex/ProductDetailController.startProductLoad';

export default class ProductDetail extends LightningElement {
    @api recordId;
    productSku = 'SKU-42';
    data;
    error;

    connectedCallback() {
        this.loadProductData();
    }

    loadProductData() {
        invokeAction(this, startProductLoad, { productSku: this.productSku })
            .then(result => {
                this.data  = JSON.parse(result);
                this.error = null;
            })
            .catch(err => {
                this.error = err.body?.message ?? 'Unknown error';
            });
    }
}
```

**Why it works:** Both HTTP requests fire in parallel on Salesforce infrastructure. Wall-clock time equals the latency of the slower of the two services (~20 seconds), not 35–40 seconds sequential. The `@AuraEnabled(continuation=true)` annotation enables the LWC continuation wire instead of a direct synchronous Apex call.

---

## Anti-Pattern: Using @future or Queueable Instead of Continuation for UI-Driven Callouts

**What practitioners do:** When facing a timeout in a Visualforce action, some practitioners move the callout into a `@future(callout=true)` method or a Queueable with `AllowsCallouts`, then poll a Custom Object for the result on page reload.

**What goes wrong:**
- The user must manually refresh the page or a polling mechanism must be built.
- The `@future` method runs in a separate transaction with no direct path to update the page without DML + page reload.
- Queueable jobs are asynchronous fire-and-forget; there is no built-in mechanism to push the result back to the originating Visualforce session.
- Adds significant complexity (result-storage SObject, polling JS, cleanup jobs) compared to the two-phase Continuation pattern.

**Correct approach:** Use `Continuation` for UI-initiated long-running callouts. The platform handles the async proxy natively. The result is returned directly to the page in the same session without polling or DML.
