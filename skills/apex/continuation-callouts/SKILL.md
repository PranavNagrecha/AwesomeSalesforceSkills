---
name: continuation-callouts
description: "Use when making long-running HTTP callouts from Visualforce or LWC that exceed the synchronous callout timeout limit, using the Apex Continuation class for async callout execution. NOT for synchronous callouts (use callouts-and-http-integrations) or queueable async patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
triggers:
  - "callout timeout exceeded in Visualforce controller"
  - "long running HTTP request from LWC component"
  - "how to make asynchronous callout from Salesforce page"
  - "Continuation class apex implementation pattern"
  - "parallel HTTP callouts from Apex Visualforce"
  - "HTTP callout taking more than 10 seconds from Apex"
tags:
  - continuation
  - async-callout
  - visualforce
  - lwc
  - http-integration
  - long-running-callout
inputs:
  - "Apex controller class or LWC Apex method requiring an HTTP callout"
  - "External service endpoint URL and authentication details (Named Credential preferred)"
  - "Whether single or parallel (up to 3) callouts are needed"
  - "Visualforce page or LWC component that invokes the callout"
outputs:
  - "Apex Continuation controller or @AuraEnabled method with startRequest/processResponse pattern"
  - "LWC component wiring for invokeAction-based continuation (if LWC context)"
  - "Checklist confirming timeout config, serializable state, and callback registration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Continuation Callouts

Use this skill when a Salesforce page (Visualforce or LWC) needs to call an external HTTP service that may take longer than the 10-second synchronous Apex callout limit allows, or when you need to fire up to three callouts in parallel without blocking the UI. The Apex `Continuation` class offloads callout execution to Salesforce infrastructure, freeing the request thread while the external service responds.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Surface type:** Is the entry point a Visualforce page action method, or an LWC `@AuraEnabled` method? The wiring differs. Visualforce uses a controller action that returns a `Continuation` object. LWC uses `invokeAction` from the Lightning Data Service continuation API.
- **Endpoint registration:** The external endpoint must be in the Remote Site Settings (or preferably a Named Credential). Continuation callouts do not bypass this requirement.
- **Most common wrong assumption:** Practitioners assume Continuation works from Apex triggers, Batch Apex, or standard `@future` methods — it does not. Continuation is exclusively for user-initiated requests from Visualforce pages or Lightning Experience components.
- **Platform limits in play:**
  - Maximum Continuation timeout: **120 seconds** per callout (configurable via `Continuation.timeout`).
  - Maximum parallel callouts per Continuation: **3**.
  - Continuation requests do not count toward the org-wide long-running synchronous request governor (since Winter '20, all callouts are excluded from that limit, so this is no longer a differentiating factor — but the 120s ceiling still applies).
  - The callback method (`processResponse`) runs in a new Apex transaction with its own governor limits.

---

## Core Concepts

### Concept 1: The Continuation Object and Two-Phase Execution

A `Continuation` request follows a two-phase pattern:

1. **Start phase** — The Visualforce action method (or LWC Apex method) creates a `Continuation` object, adds one or more `HttpRequest` objects to it, sets the callback method name, and returns it. Salesforce intercepts the return value, fires the HTTP request(s) off-platform, and releases the request thread.
2. **Callback phase** — When the external service responds (or the timeout elapses), Salesforce invokes the callback method in a fresh Apex execution context. The callback receives the response via `Continuation.getResponse(label)` and returns the final value to the page.

The Salesforce platform acts as a proxy. The request thread is freed between phases, so no page timeout occurs while waiting for the external service.

### Concept 2: State Passing Between Phases

Because the callback runs in a new transaction, instance variables on a Visualforce controller are not automatically preserved. State must be passed explicitly:

- Set `continuation.state` to any serializable Apex object (String, Map, custom class with `JSON.serialize`-compatible structure) before returning from the start method.
- In the callback, retrieve it from the `state` parameter: `public Object processResponse(List<String> labels, Object state)`.
- **Non-serializable types (Blob, SObject with relationship fields, iterators) cannot be passed as state.** This is a common source of runtime failures.

### Concept 3: Parallel Callouts

A single `Continuation` can encapsulate up to **three simultaneous HTTP requests**. Each call to `continuation.addHttpRequest(req)` returns a unique String label. All requests in the batch fire in parallel. The callback receives a `List<String> labels` and uses `Continuation.getResponse(label)` to retrieve the individual responses. Order of response arrival is non-deterministic; always retrieve by label, not by index.

### Concept 4: Visualforce vs. LWC Invocation

| Context | How to invoke |
|---|---|
| Visualforce | Action method returns `Continuation`. The page uses `action="{!startContinuation}"`. |
| LWC (Aura-compatible) | Import the Apex method and call `invokeAction()` from the LWC JavaScript, which wraps the continuation wire. The Apex method must be annotated `@AuraEnabled(continuation=true)`. |

---

## Common Patterns

### Pattern 1: Single Continuation Callout from Visualforce Controller

**When to use:** A Visualforce page button triggers a callout to a slow external REST API (e.g., a quote-generation service that routinely takes 30–90 seconds).

**How it works:**

```apex
public class QuoteContinuationController {

    // State to pass between phases — must be serializable
    public String quoteRequestId { get; set; }
    public String quoteResult    { get; set; }

    // Phase 1 — Start the callout, return Continuation
    public Continuation startQuoteCallout() {
        // Max timeout in seconds (1–120). Default is 30.
        Continuation con = new Continuation(60);
        // Name of the callback method on THIS class
        con.continuationMethod = 'processQuoteResponse';

        HttpRequest req = new HttpRequest();
        req.setMethod('POST');
        req.setEndpoint('callout:QuoteService/api/quotes'); // Named Credential
        req.setHeader('Content-Type', 'application/json');
        req.setBody('{"requestId":"' + quoteRequestId + '"}');

        con.addHttpRequest(req);

        // Pass serializable state to the callback
        con.state = quoteRequestId;

        return con; // Salesforce intercepts and fires the HTTP request
    }

    // Phase 2 — Callback after callout completes
    public Object processQuoteResponse(List<String> labels, Object state) {
        // labels[0] is the label for the first (and only) request
        HttpResponse res = Continuation.getResponse(labels[0]);

        if (res.getStatusCode() == 200) {
            quoteResult = res.getBody();
        } else {
            quoteResult = 'Error: ' + res.getStatusCode();
        }

        // Return null or a PageReference to navigate after callback
        return null;
    }
}
```

**Visualforce page binding:**
```xml
<apex:page controller="QuoteContinuationController">
    <apex:form>
        <apex:commandButton value="Generate Quote"
                            action="{!startQuoteCallout}"
                            reRender="resultPanel"/>
        <apex:outputPanel id="resultPanel">
            <apex:outputText value="{!quoteResult}"/>
        </apex:outputPanel>
    </apex:form>
</apex:page>
```

**Why not the alternative:** A synchronous `Http.send()` in a Visualforce action method times out at 10 seconds and blocks the Salesforce request thread. For slow services, this causes `System.CalloutException: Read timed out` before the service responds.

---

### Pattern 2: Parallel Callouts from a Single Continuation

**When to use:** A dashboard page needs to aggregate data from three different APIs simultaneously (e.g., ERP inventory, CRM pricing, logistics tracking). Firing them sequentially wastes time.

**How it works:**

```apex
public class DashboardContinuationController {

    public String inventoryData  { get; set; }
    public String pricingData    { get; set; }
    public String trackingData   { get; set; }

    private String inventoryLabel;
    private String pricingLabel;
    private String trackingLabel;

    public Continuation startDashboardLoad() {
        Continuation con = new Continuation(90);
        con.continuationMethod = 'processDashboardResponses';

        HttpRequest invReq = new HttpRequest();
        invReq.setMethod('GET');
        invReq.setEndpoint('callout:ERPService/inventory');
        inventoryLabel = con.addHttpRequest(invReq); // store label

        HttpRequest priceReq = new HttpRequest();
        priceReq.setMethod('GET');
        priceReq.setEndpoint('callout:PricingService/current');
        pricingLabel = con.addHttpRequest(priceReq);

        HttpRequest trackReq = new HttpRequest();
        trackReq.setMethod('GET');
        trackReq.setEndpoint('callout:LogisticsService/track');
        trackingLabel = con.addHttpRequest(trackReq);

        // Pass labels as state so callback can retrieve by name
        con.state = new Map<String, String>{
            'inv'   => inventoryLabel,
            'price' => pricingLabel,
            'track' => trackingLabel
        };

        return con;
    }

    public Object processDashboardResponses(List<String> labels, Object state) {
        Map<String, String> labelMap = (Map<String, String>) state;

        HttpResponse invRes   = Continuation.getResponse(labelMap.get('inv'));
        HttpResponse priceRes = Continuation.getResponse(labelMap.get('price'));
        HttpResponse trackRes = Continuation.getResponse(labelMap.get('track'));

        inventoryData = invRes.getStatusCode()  == 200 ? invRes.getBody()  : 'Error';
        pricingData   = priceRes.getStatusCode() == 200 ? priceRes.getBody() : 'Error';
        trackingData  = trackRes.getStatusCode() == 200 ? trackRes.getBody() : 'Error';

        return null;
    }
}
```

**Why not sequential:** Three sequential Continuation calls would require three separate user interactions or a chained pattern. Using a single `Continuation` with three requests fires them in parallel on Salesforce infrastructure, typically reducing wall-clock latency to the slowest single response rather than the sum of all three.

---

### Pattern 3: LWC with @AuraEnabled Continuation

**When to use:** A Lightning Web Component (not Visualforce) needs to invoke a long-running callout. Available since Summer '19.

**How it works:**

```apex
// Apex controller
public with sharing class ProductSearchController {

    @AuraEnabled(continuation=true)
    public static Object startSearch(String searchTerm) {
        Continuation con = new Continuation(60);
        con.continuationMethod = 'processSearchResults';

        HttpRequest req = new HttpRequest();
        req.setMethod('GET');
        req.setEndpoint('callout:ProductCatalog/search?q=' +
                        EncodingUtil.urlEncode(searchTerm, 'UTF-8'));
        con.addHttpRequest(req);

        con.state = searchTerm;
        return con;
    }

    @AuraEnabled(continuation=true)
    public static Object processSearchResults(List<String> labels, Object state) {
        HttpResponse res = Continuation.getResponse(labels[0]);
        if (res.getStatusCode() == 200) {
            return res.getBody();
        }
        throw new AuraHandledException('Search failed: ' + res.getStatusCode());
    }
}
```

```javascript
// LWC JavaScript — productSearch.js
import { LightningElement } from 'lwc';
import { invokeAction }      from 'lightning/actions'; // Aura-compatible wire
import startSearch            from '@salesforce/apex/ProductSearchController.startSearch';

export default class ProductSearch extends LightningElement {
    results;

    handleSearch(event) {
        const term = event.target.value;
        invokeAction(this, startSearch, { searchTerm: term })
            .then(result => { this.results = result; })
            .catch(error => console.error(error));
    }
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Callout expected < 10 seconds, from Apex trigger or batch | Synchronous `Http.send()` or Queueable Apex | Continuation is not supported in triggers or async contexts |
| Callout expected 10–120 seconds, from Visualforce | `Continuation` object in controller action method | Only mechanism that frees the VF request thread |
| Callout expected 10–120 seconds, from LWC | `@AuraEnabled(continuation=true)` + `invokeAction` | LWC equivalent of VF Continuation; same 120s ceiling |
| 2–3 independent callouts needed simultaneously, from UI | Single `Continuation` with multiple `addHttpRequest` calls | Fires in parallel; reduces latency vs. sequential calls |
| Callout expected > 120 seconds | Polling pattern: trigger async job, poll status endpoint | Platform hard ceiling is 120 seconds; Continuation cannot exceed it |
| From Apex trigger, Batch, Scheduled, @future | Standard synchronous callout or Queueable with callout=true | Continuation requires a user-initiated HTTP request context |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `Continuation` object timeout set explicitly (1–120 seconds); not left at default 30 if service needs more.
- [ ] `continuationMethod` name matches the actual callback method signature exactly.
- [ ] Callback method signature is `public Object methodName(List<String> labels, Object state)`.
- [ ] All state passed between phases is JSON-serializable (no Blob, no SObject with relationship queries).
- [ ] Each `addHttpRequest` return label is stored and used to retrieve the correct response in the callback.
- [ ] Endpoint is registered in Remote Site Settings or uses a Named Credential.
- [ ] Error status codes handled in the callback (service may return 4xx/5xx on timeout or failure).
- [ ] For LWC: Apex method annotated `@AuraEnabled(continuation=true)`, not plain `@AuraEnabled`.
- [ ] Continuation is NOT used from a trigger, batch, scheduled, or `@future` context.
- [ ] Test class uses `Test.setContinuationResponse()` and `Test.invokeContinuationMethod()` to mock both phases.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Continuation is not supported in triggers or async Apex** — Attempting to instantiate `Continuation` from a trigger, Batch Apex `execute`, Scheduled Apex, or `@future` method throws a runtime exception. The class is only valid in the context of a Visualforce action request or LWC `@AuraEnabled(continuation=true)` invocation.

2. **Non-serializable state silently fails or throws at callback time** — The `state` property is serialized by the platform between phases. Passing an SObject that includes relationship query results, a `Type` reference, or an `Iterator` causes a `System.SerializationException` at callback invocation. Always pass simple scalar types, `Map<String, String>`, or a plain class with `@TestVisible` and primitive fields.

3. **Callback method must be public and on the same class** — `continuationMethod` must be a `public` (not private) method on the same Apex class. It cannot be a static method. If the name is misspelled or the method is private, the callback silently never fires — no exception is thrown at start time.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex controller with `startRequest`/`processResponse` | Visualforce or LWC Apex class implementing the two-phase Continuation pattern |
| Visualforce page with `action` binding | Page XML wiring the action method and output panel rerender |
| LWC component with `invokeAction` | JavaScript component using the continuation-aware import |
| `check_continuation_callouts.py` report | Static analysis of Apex classes for Continuation anti-patterns |

---

## Related Skills

- `apex/callouts-and-http-integrations` — use for synchronous HTTP callouts under 10 seconds, Named Credential setup, and `HttpRequest`/`HttpResponse` fundamentals.
- `apex/async-apex` — use when the core design choice is whether the callout belongs in `@future`, Queueable, Batch, or Scheduled Apex (none of which support Continuation).
- `apex/exception-handling` — use when callback error handling and retry logic need a structured pattern.
- `apex/test-class-standards` — use for mocking Continuation responses in test classes with `Test.setContinuationResponse()`.
