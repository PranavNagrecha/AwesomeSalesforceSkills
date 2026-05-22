# LLM Anti-Patterns — Apex WSDL-to-Apex Patterns

Common mistakes AI coding assistants make when generating or advising on outbound SOAP integrations built with the wsdl2apex tool. Use this as a self-check before returning generated code.

## Anti-Pattern 1: Using `HttpCalloutMock` to mock a SOAP callout

**What the LLM generates:**

```apex
@isTest
private class MyServiceTest {
    static testMethod void testCallout() {
        Test.setMock(HttpCalloutMock.class, new MyCalloutMock());  // WRONG for SOAP
        Test.startTest();
        new MyServiceWrapper().doSomething();
        Test.stopTest();
    }
}
```

**Why it happens:** The model has seen far more `HttpCalloutMock` test examples (REST is the dominant Salesforce integration pattern in public training data) and falls back to that mock without checking that the underlying callout uses a wsdl2apex-generated stub. The compile path also doesn't fail — only runtime does.

**Correct pattern:**

```apex
Test.setMock(WebServiceMock.class, new MyServiceWebServiceMock());

// And the mock implements WebServiceMock, not HttpCalloutMock:
public class MyServiceWebServiceMock implements WebServiceMock {
    public void doInvoke(
        Object stub, Object request, Map<String, Object> response,
        String endpoint, String soapAction, String requestName,
        String responseNS, String responseName, String responseType
    ) {
        // ... populate response.put('response_x', element) ...
    }
}
```

**Detection hint:** Grep generated test code for `HttpCalloutMock`. If the code under test imports any class whose source contains `_x` properties (`endpoint_x`, `timeout_x`), the mock interface is wrong.

---

## Anti-Pattern 2: Setting the Authorization header in `inputHttpHeaders_x` when using a Named Credential

**What the LLM generates:**

```apex
stub.endpoint_x = 'callout:My_Service';
stub.inputHttpHeaders_x = new Map<String,String>{
    'Authorization' => 'Bearer ' + getAccessToken(),
    'SOAPAction'    => 'urn:DoThing'
};
```

**Why it happens:** REST-pattern muscle memory — the model assumes the Authorization header is always set inline. It hasn't internalized that `endpoint_x = 'callout:<NC>'` delegates auth to the Named Credential, and that mixing the two paths causes silent strip-out of the developer's Authorization header.

**Correct pattern:**

```apex
// Auth lives in the Named Credential / External Credential. Period.
stub.endpoint_x = 'callout:My_Service';
stub.inputHttpHeaders_x = new Map<String,String>{
    'SOAPAction' => 'urn:DoThing'
    // No Authorization here — the NC injects it.
};
```

**Detection hint:** Search the generated wrapper for `inputHttpHeaders_x` and the literal `'Authorization'` key on the same code path that sets `endpoint_x = 'callout:'`. Either one or the other — never both.

---

## Anti-Pattern 3: Catching `CalloutException` for SOAP faults

**What the LLM generates:**

```apex
try {
    MyServicePort.Response r = stub.doSomething(args);
} catch (CalloutException e) {
    // Assumes this catches SOAP faults
    logger.warn('SOAP error: ' + e.getMessage());
}
```

**Why it happens:** The model conflates "any callout error" with `CalloutException`. It hasn't internalized that `System.WebServiceCalloutException` is a distinct class with fault-specific metadata, and that catching the broader `CalloutException` swallows the fault without preserving the `<faultcode>` / `<faultstring>`.

**Correct pattern:**

```apex
try {
    MyServicePort.Response r = stub.doSomething(args);
} catch (System.WebServiceCalloutException fault) {
    // <faultcode> / <faultstring> — vendor returned a business error
    logger.error('SOAP fault: ' + fault.getMessage());
} catch (System.CalloutException net) {
    // Transport-level — timeout, DNS, TLS, non-2xx without SOAP body
    logger.error('Network: ' + net.getMessage());
}
```

**Detection hint:** Look for outbound SOAP code that has only one `catch` block. Either it catches `Exception` (too broad) or `CalloutException` (misses faults). Both are wrong — the canonical pattern is two `catch` blocks, `WebServiceCalloutException` first.

---

## Anti-Pattern 4: Hardcoding the endpoint URL in `endpoint_x`

**What the LLM generates:**

```apex
MyServicePort.Soap stub = new MyServicePort.Soap();
stub.endpoint_x = 'https://api.example.com/v1/Service.svc';  // literal URL
stub.timeout_x  = 30000;
```

**Why it happens:** The WSDL bakes the vendor's URL into the generated stub as the default, and the model copies that URL into the wrapper to "be explicit". Public examples often show this pattern because they predate Named Credentials becoming the standard.

**Correct pattern:**

```apex
MyServicePort.Soap stub = new MyServicePort.Soap();
stub.endpoint_x = 'callout:My_Service_NC';  // Named Credential
stub.timeout_x  = 30000;
```

**Detection hint:** Grep the wrapper for `endpoint_x = 'https`. The literal `https://` should never appear after `endpoint_x =`. The only acceptable RHS is `'callout:<Name>'`.

---

## Anti-Pattern 5: Hand-editing the generated stub instead of pre-processing the WSDL

**What the LLM generates:** When a developer reports `xsd:choice` errors, the model suggests:

```
Open MyServicePort.cls in the IDE and replace the inner class
Discount with a manually-written version that has both fields as
optional. Save and continue.
```

**Why it happens:** The model treats the generated `.cls` file as ordinary Apex source. It doesn't recognize that the file is regenerated wholesale by Setup > Apex Classes > Generate from WSDL — every hand-edit is destroyed on the next regen.

**Correct pattern:**

The fix belongs in the WSDL on disk, not the generated Apex:

```xml
<!-- Edit MyService.wsdl, then re-run Generate from WSDL -->
<xsd:complexType name="Discount">
  <xsd:sequence>
    <xsd:element name="PercentageOff" type="xsd:decimal" minOccurs="0"/>
    <xsd:element name="FlatAmount"    type="xsd:decimal" minOccurs="0"/>
  </xsd:sequence>
</xsd:complexType>
```

Persist the cleaned WSDL alongside the project with a `WSDL_README.md` describing every edit applied.

**Detection hint:** Any LLM advice that says "edit the generated class" / "change line N of MyServicePort.cls" is wrong. The correct advice is "edit the WSDL file and regenerate."

---

## Anti-Pattern 6: Forgetting `timeout_x` and inheriting the 10-second default

**What the LLM generates:**

```apex
MyServicePort.Soap stub = new MyServicePort.Soap();
stub.endpoint_x = 'callout:My_NC';
MyServicePort.Result r = stub.doExpensiveOperation(payload);  // No timeout_x set
```

**Why it happens:** The model treats `timeout_x` as optional because the WSDL doesn't declare a timeout — the default of 10 s is invisible in the generated source.

**Correct pattern:**

```apex
MyServicePort.Soap stub = new MyServicePort.Soap();
stub.endpoint_x = 'callout:My_NC';
stub.timeout_x  = 60000;  // 60 s; max is 120000
MyServicePort.Result r = stub.doExpensiveOperation(payload);
```

**Detection hint:** Grep wrapper code for `new <Stub>Port.<Port>()` and verify a `.timeout_x =` line follows within 5 lines. Missing timeout assignment is a smell — the default is almost never correct for SOAP services.
