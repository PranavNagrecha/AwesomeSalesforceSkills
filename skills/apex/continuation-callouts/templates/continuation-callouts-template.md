# Continuation Callouts — Work Template

Use this template when implementing or reviewing an Apex Continuation callout.

---

## Scope

**Skill:** `apex/continuation-callouts`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before writing any code:

- **Entry point type:** [ ] Visualforce controller action  [ ] LWC `@AuraEnabled(continuation=true)`
- **External endpoint URL / Named Credential name:** ___________________________
- **Endpoint registered in Remote Site Settings or Named Credential?** [ ] Yes  [ ] No — must add before deploying
- **Expected service response time (P99):** ___________ seconds
- **Continuation timeout to set:** ___________ seconds (max 120; recommend 1.5–2x P99)
- **Number of parallel callouts needed:** [ ] 1  [ ] 2  [ ] 3  [ ] >3 (requires chaining — document separately)
- **State to pass between phases (must be serializable):** ___________________________
- **Known constraints or limits in play:** ___________________________

---

## Apex Controller Template (Visualforce)

```apex
public class {{ControllerName}} {

    // --- State fields visible to the page ---
    public String {{resultField}} { get; set; }
    public Boolean hasError       { get; set; }

    // --- Phase 1: Start the continuation ---
    public Continuation {{startMethodName}}() {
        hasError = false;

        // Set timeout (seconds). Max: 120. Adjust to match service P99 + buffer.
        Continuation con = new Continuation({{timeoutSeconds}});
        con.continuationMethod = '{{callbackMethodName}}';

        HttpRequest req = new HttpRequest();
        req.setMethod('{{GET_OR_POST}}');
        req.setEndpoint('callout:{{NamedCredentialName}}/{{path}}');
        // req.setHeader('Content-Type', 'application/json');
        // req.setBody(JSON.serialize(payloadMap));

        con.addHttpRequest(req);

        // Pass only JSON-serializable state (String, Map<String,String>, etc.)
        con.state = '{{serializableStateValue}}';

        return con; // Platform dispatches the HTTP request; thread is freed
    }

    // --- Phase 2: Callback after HTTP response arrives ---
    // Signature is fixed — do not change parameter types or make this static/private
    public Object {{callbackMethodName}}(List<String> labels, Object state) {
        String savedState = (String) state; // cast to your actual state type

        HttpResponse res = Continuation.getResponse(labels[0]);

        if (res.getStatusCode() == 200) {
            {{resultField}} = res.getBody(); // or parse JSON as needed
        } else {
            hasError      = true;
            {{resultField}} = 'Error: HTTP ' + res.getStatusCode();
        }

        return null; // null = re-render page; PageReference = navigate
    }
}
```

---

## Apex Controller Template (LWC — @AuraEnabled)

```apex
public with sharing class {{ControllerName}} {

    @AuraEnabled(continuation=true)
    public static Object {{startMethodName}}({{paramType}} {{paramName}}) {
        Continuation con = new Continuation({{timeoutSeconds}});
        con.continuationMethod = '{{callbackMethodName}}';

        HttpRequest req = new HttpRequest();
        req.setMethod('{{GET_OR_POST}}');
        req.setEndpoint('callout:{{NamedCredentialName}}/{{path}}');
        con.addHttpRequest(req);

        // State: simple serializable value or JSON string
        con.state = String.valueOf({{paramName}});

        return con;
    }

    @AuraEnabled(continuation=true)
    public static Object {{callbackMethodName}}(List<String> labels, Object state) {
        HttpResponse res = Continuation.getResponse(labels[0]);
        if (res.getStatusCode() == 200) {
            return res.getBody(); // or JSON.deserializeUntyped(res.getBody())
        }
        throw new AuraHandledException('Callout failed: HTTP ' + res.getStatusCode());
    }
}
```

---

## Parallel Callout Extension (up to 3 requests)

```apex
// In Phase 1, add up to 3 requests:
String label1 = con.addHttpRequest(req1); // first callout
String label2 = con.addHttpRequest(req2); // second callout
String label3 = con.addHttpRequest(req3); // third callout (max)

// Pass labels in state so callback can retrieve by semantic name
con.state = new Map<String, String>{
    'svc1' => label1,
    'svc2' => label2,
    'svc3' => label3
};

// In Phase 2 (callback):
Map<String, String> ctx = (Map<String, String>) state;
HttpResponse res1 = Continuation.getResponse(ctx.get('svc1'));
HttpResponse res2 = Continuation.getResponse(ctx.get('svc2'));
HttpResponse res3 = Continuation.getResponse(ctx.get('svc3'));
```

---

## Visualforce Page Binding Template

```xml
<apex:page controller="{{ControllerName}}">
    <apex:form>
        <!-- Optional input fields -->
        <apex:inputText value="{!{{inputField}}}" label="{{InputLabel}}"/>

        <!-- Action button that triggers Phase 1 -->
        <apex:commandButton value="{{ButtonLabel}}"
                            action="{!{{startMethodName}}}"
                            reRender="resultPanel"/>

        <!-- Result panel re-rendered after Phase 2 callback -->
        <apex:outputPanel id="resultPanel">
            <apex:outputText value="{!{{resultField}}}" rendered="{!!hasError}"/>
            <apex:outputText value="{!{{resultField}}}" styleClass="errorText"
                             rendered="{!hasError}"/>
        </apex:outputPanel>
    </apex:form>
</apex:page>
```

---

## LWC JavaScript Template

```javascript
import { LightningElement } from 'lwc';
import { invokeAction }     from 'lightning/actions';
import {{startMethodName}}  from '@salesforce/apex/{{ControllerName}}.{{startMethodName}}';

export default class {{ComponentName}} extends LightningElement {
    result;
    error;

    handleInvoke() {
        invokeAction(this, {{startMethodName}}, { {{paramName}}: this.{{localProp}} })
            .then(result => {
                this.result = result;
                this.error  = null;
            })
            .catch(err => {
                this.error  = err.body?.message ?? 'Unknown error';
                this.result = null;
            });
    }
}
```

---

## Test Class Template

```apex
@IsTest
static void test{{StartMethodName}}Success() {
    {{ControllerName}} ctrl = new {{ControllerName}}();
    // Set any required input fields
    // ctrl.{{inputField}} = 'test-value';

    // Phase 1
    Continuation con = (Continuation) ctrl.{{startMethodName}}();
    System.assertNotEquals(null, con, 'Continuation should be returned');

    // Inject mock HTTP response
    HttpResponse mockRes = new HttpResponse();
    mockRes.setStatusCode(200);
    mockRes.setBody('{{expectedResponseBody}}');

    String label = con.requests.keySet().iterator().next();
    Test.setContinuationResponse(label, mockRes);

    // Phase 2
    Object returnVal = Test.invokeContinuationMethod(ctrl, con);

    // Assert
    System.assertEquals(null, returnVal, 'Callback should return null for same-page render');
    System.assertEquals(false, ctrl.hasError, 'No error expected for HTTP 200');
    // System.assert(ctrl.{{resultField}}.contains('expected content'));
}
```

---

## Review Checklist

Copy and check off each item before closing the task:

- [ ] Continuation timeout set explicitly; value matches service P99 + buffer, not exceeding 120 seconds.
- [ ] `continuationMethod` name is spelled correctly and matches the actual callback method name.
- [ ] Callback signature is exactly `public Object name(List<String> labels, Object state)` — public, non-static.
- [ ] State value is JSON-serializable (no SObject with relationship fields, no Blob, no Type reference).
- [ ] `addHttpRequest` called at most 3 times per Continuation (4+ throws a limit exception).
- [ ] Endpoint uses a Named Credential or is registered in Remote Site Settings.
- [ ] HTTP error status codes (4xx, 5xx) handled in callback; `hasError` or `AuraHandledException` used appropriately.
- [ ] For LWC: Apex method annotated `@AuraEnabled(continuation=true)`.
- [ ] Continuation not used in trigger, batch, scheduled, or @future context.
- [ ] Test class covers Phase 1 and Phase 2 using `Test.setContinuationResponse()` and `Test.invokeContinuationMethod()`.
- [ ] `check_continuation_callouts.py` run against metadata directory; all issues resolved.

---

## Notes

Record any deviations from the standard pattern and why:

(fill in)
