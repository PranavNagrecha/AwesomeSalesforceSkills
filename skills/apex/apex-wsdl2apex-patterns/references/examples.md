# Examples — Apex WSDL-to-Apex Patterns

## Example 1: WSDL pre-processing and stub generation, then Named-Credential dispatch

**Context:** A finance team has integrated a third-party tax engine that exposes a SOAP API. The vendor ships a single `TaxEngine.wsdl` containing two ports (`Quote`, `Commit`). The WSDL is 380 KB and contains one `xsd:choice` element on a discount discriminator.

**Problem:** First attempt — uploading the raw WSDL to Setup > Apex Classes > Generate from WSDL fails with:

```
Error: Failed to parse wsdl: schema does not support 'choice'
```

Hand-editing the generated Apex isn't possible because the parser doesn't even produce a class — it rejected the WSDL outright. The team had also planned to set the `endpoint_x` directly to the vendor's production URL.

**Solution:**

```xml
<!-- BEFORE — TaxEngine.wsdl, lines 412-419 -->
<xsd:complexType name="Discount">
  <xsd:choice>
    <xsd:element name="PercentageOff" type="xsd:decimal"/>
    <xsd:element name="FlatAmount"    type="xsd:decimal"/>
  </xsd:choice>
</xsd:complexType>

<!-- AFTER — keep both branches as optional siblings -->
<xsd:complexType name="Discount">
  <xsd:sequence>
    <xsd:element name="PercentageOff" type="xsd:decimal" minOccurs="0"/>
    <xsd:element name="FlatAmount"    type="xsd:decimal" minOccurs="0"/>
  </xsd:sequence>
</xsd:complexType>
```

Then regenerate:

```apex
// Wrapper service — NOT the generated stub.
public with sharing class TaxEngineService {
    public class Result {
        public Decimal computedTax;
        public String  errorMessage;
        public Boolean isFault;
    }

    public Result quote(Id orderId, Decimal subtotal, String state) {
        TaxEnginePort.Quote stub = new TaxEnginePort.Quote();
        stub.endpoint_x = 'callout:Tax_Engine_NC';      // NEVER a literal URL
        stub.timeout_x  = 60000;                         // 60 s — vendor SLA is 30 s p99
        stub.inputHttpHeaders_x = new Map<String,String>{
            'X-Idempotency-Key' => orderId
        };

        Result r = new Result();
        try {
            TaxEnginePort.QuoteResponse_element resp =
                stub.GetQuote(subtotal, state);
            r.computedTax = resp.TaxAmount;
        } catch (System.WebServiceCalloutException fault) {
            // SOAP fault — server returned <faultcode>/<faultstring>
            r.isFault = true;
            r.errorMessage = fault.getMessage();
        } catch (System.CalloutException net) {
            // Transport-level failure (timeout, DNS, TLS, non-2xx without SOAP body)
            r.isFault = false;
            r.errorMessage = 'NETWORK: ' + net.getMessage();
        }
        return r;
    }
}
```

The Named Credential `Tax_Engine_NC` resolves both the URL and the auth (OAuth client credentials via External Credential). Production deploys do not touch `endpoint_x` — promoting between sandboxes just changes the NC.

**Why it works:** Pre-processing the WSDL on disk preserves the regen workflow — the vendor's next WSDL update is applied to the cleaned WSDL via diff, not to the generated Apex. Routing through a Named Credential decouples auth and endpoint from code, and the two-catch ladder correctly differentiates SOAP faults (vendor returned a business error) from transport failures (timeout, DNS) — these warrant different retry strategies.

---

## Example 2: Mocking the outbound SOAP call in a unit test

**Context:** A regression test for an Apex trigger that fires the tax-engine wrapper above whenever an `Order__c` transitions to `Committed`. The team's first attempt used `Test.setMock(HttpCalloutMock.class, new TaxEngineRestMock())` because that's the pattern they used for the REST integrations elsewhere.

**Problem:** The test compiled but threw at runtime:

```
System.CalloutException: Methods defined as TestMethod do not support Web service callouts
```

`HttpCalloutMock` only intercepts `Http.send()`; the wsdl2apex-generated stub goes through a separate runtime path and ignores it. SOAP callouts must use `WebServiceMock`.

**Solution:**

```apex
@isTest
public class TaxEngineMock implements WebServiceMock {
    public Decimal taxToReturn;
    public Boolean throwFault = false;

    public TaxEngineMock(Decimal tax) { this.taxToReturn = tax; }

    public void doInvoke(
        Object stub, Object request, Map<String, Object> response,
        String endpoint, String soapAction, String requestName,
        String responseNS, String responseName, String responseType
    ) {
        if (throwFault) {
            // Simulate a SOAP fault — runtime translates this to WebServiceCalloutException
            throw new System.CalloutException('soap:Server INVALID_ZIP');
        }
        TaxEnginePort.QuoteResponse_element resp =
            new TaxEnginePort.QuoteResponse_element();
        resp.TaxAmount = taxToReturn;
        response.put('response_x', resp);   // literal key 'response_x' is the contract
    }
}

@isTest
private class TaxEngineService_Test {
    @isTest static void quote_happyPath_returnsTaxAmount() {
        Test.setMock(WebServiceMock.class, new TaxEngineMock(8.25));
        Test.startTest();
        TaxEngineService.Result r =
            new TaxEngineService().quote('001xx0000000001', 100.00, 'CA');
        Test.stopTest();

        System.assertEquals(8.25, r.computedTax);
        System.assertEquals(false, r.isFault);
    }

    @isTest static void quote_soapFault_recordsErrorWithoutThrowing() {
        TaxEngineMock mock = new TaxEngineMock(0);
        mock.throwFault = true;
        Test.setMock(WebServiceMock.class, mock);

        Test.startTest();
        TaxEngineService.Result r =
            new TaxEngineService().quote('001xx0000000002', 100.00, 'XX');
        Test.stopTest();

        System.assertEquals(true, r.isFault);
        System.assert(r.errorMessage.contains('INVALID_ZIP'));
    }
}
```

**Why it works:** `WebServiceMock` is the only interface the SOAP runtime checks. The `response.put('response_x', element)` key is hardcoded into the runtime — using any other key returns null and the caller sees an NPE that looks like a generated-stub bug. Throwing a `CalloutException` from inside `doInvoke()` is the documented way to simulate a SOAP fault since `WebServiceCalloutException` has no public constructor.

---

## Example 3: WSDL too large to compile — split by operation

**Context:** A vendor's `Inventory.wsdl` is 920 KB and declares 47 operations across 3 ports. The integration only uses 4 operations from one port (`StockLookup`).

**Problem:** Generate from WSDL succeeds in parsing the WSDL itself (under 1 MB) but the resulting Apex stub exceeds the 1 MB class file limit and Save fails:

```
Error: Apex class is too large. Maximum size is 6,000,000 characters / 1,000,000 bytes compiled.
```

The team would still need to deploy the generated class through metadata API, where the same limit applies.

**Solution:** Strip the WSDL to only the operations actually consumed. The general process:

1. Copy `Inventory.wsdl` to `Inventory-StockLookup.wsdl`.
2. Delete every `<wsdl:operation>` from the `StockLookup` binding except the four needed: `GetStock`, `ReserveStock`, `ReleaseStock`, `CommitReservation`.
3. Delete the entire `<wsdl:binding>` blocks for the two unused ports (`OrderManagement`, `WarehouseAdmin`).
4. Walk the `<xsd:complexType>` definitions and delete any type only referenced by deleted operations. Iteratively re-validate the WSDL — types referenced by retained types must stay.
5. Re-run Generate from WSDL on the trimmed WSDL. Stub size drops to ~180 KB.

```apex
// Wrapper for the trimmed stub
public with sharing class InventoryStockLookup {
    private final InventoryStockLookupPort.StockLookup stub;

    public InventoryStockLookup() {
        this.stub = new InventoryStockLookupPort.StockLookup();
        this.stub.endpoint_x = 'callout:Inventory_NC';
        this.stub.timeout_x  = 30000;
    }

    public Integer getStock(String sku) {
        InventoryStockLookupPort.GetStockResponse_element r = stub.GetStock(sku);
        return (Integer) r.Quantity;
    }
}
```

**Why it works:** The trimmed WSDL is the single source of truth for the integration's surface area — operations that aren't represented in the WSDL cannot be silently added by a developer who guesses at the API. The vendor's full WSDL is preserved in source control as `Inventory-vendor-FULL.wsdl` so the next operation addition is auditable.

---

## Anti-Pattern: Hand-edit the generated stub instead of the WSDL

**What practitioners do:** Open the generated `MyServicePort.cls` in the IDE, add a method, rename a `_x` field, or convert a `Decimal` to `Double` to match a downstream consumer. Save the class. Move on.

**What goes wrong:** The next vendor WSDL revision triggers a regen. The developer runs Generate from WSDL, overwrites the stub, and loses every hand-edit. The regression isn't caught until production because the test class is also out of date.

**Correct approach:** Treat the generated stub as **generated code**. Apply edits to the WSDL on disk and regenerate, or add the missing behavior in the wrapper class where customization is regen-safe. If the WSDL itself needs structural fixes (e.g. converting `xsd:choice`), commit the cleaned WSDL alongside the project with a `WSDL_README.md` documenting which edits were applied, so the next regen starts from the cleaned WSDL — not the vendor's original.
