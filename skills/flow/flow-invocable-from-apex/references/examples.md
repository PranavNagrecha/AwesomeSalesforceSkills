# Examples — Flow Invocable From Apex

## Example 1: Bulk-safe account enrichment

**Context:** A record-triggered flow on Account needs to look up an industry code from a protected Custom Metadata type and copy it onto the account. The lookup itself is complex enough that it belongs in Apex, but the overall flow should stay declarative.

**Problem:** Admin first wrote the invocable as `static String lookup(String industry)`. Flow refused to use it because the signature doesn't match the bulk contract. Admin switched to `static List<String> lookup(List<String> industries)` — compiles, but when 200 accounts save at once, the invocable still does a SOQL inside a per-request loop and hits 101-SOQL limits.

**Solution:**

```apex
public class IndustryLookupInvocable {
    public class Request {
        @InvocableVariable(required=true label='Industry Input')
        public String industry;
    }
    public class Response {
        @InvocableVariable(label='Industry Code')
        public String code;
        @InvocableVariable(label='Industry Description')
        public String description;
    }

    @InvocableMethod(label='Look Up Industry Code', category='Data Hygiene')
    public static List<Response> lookup(List<Request> requests) {
        if (requests == null || requests.isEmpty()) return new List<Response>();

        Set<String> industries = new Set<String>();
        for (Request r : requests) industries.add(r.industry);

        // ONE SOQL regardless of input size.
        Map<String, Industry_Code__mdt> byLabel = new Map<String, Industry_Code__mdt>();
        for (Industry_Code__mdt row :
                [SELECT Label, Code__c, Description__c
                 FROM Industry_Code__mdt
                 WHERE Label IN :industries]) {
            byLabel.put(row.Label, row);
        }

        List<Response> results = new List<Response>();
        for (Request r : requests) {
            Response resp = new Response();
            Industry_Code__mdt row = byLabel.get(r.industry);
            if (row != null) {
                resp.code = row.Code__c;
                resp.description = row.Description__c;
            }
            results.add(resp);
        }
        return results;
    }
}
```

**Why it works:** Single SOQL regardless of whether 1 or 200 accounts triggered the flow. Output list order matches input list order, so Flow's Loop element can walk both together. Nulls become empty responses instead of exceptions.

---

## Example 2: Invocable that calls a vendor API

**Context:** A flow needs to geocode addresses by calling an external vendor. Callouts are not allowed inline from an after-save trigger context.

**Problem:** Without `callout=true`, Flow won't let the action be used from a trigger-initiated context at all. And the invocable as-written issues a callout per request, blowing the 100-callout limit at the first large bulk save.

**Solution:**

```apex
public class GeocodeInvocable {
    public class Request {
        @InvocableVariable(required=true) public Id accountId;
        @InvocableVariable(required=true) public String address;
    }
    public class Response {
        @InvocableVariable public Decimal lat;
        @InvocableVariable public Decimal lng;
        @InvocableVariable public String error;
    }

    @InvocableMethod(
        label='Geocode Address',
        callout=true,                         // REQUIRED for callouts
        category='Address Hygiene'
    )
    public static List<Response> geocode(List<Request> requests) {
        List<Response> results = new List<Response>();
        if (requests == null || requests.isEmpty()) return results;

        // Batch the upstream call (vendor supports batch geocoding).
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Geocoder/v1/batch');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(buildBatchPayload(requests)));

        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() != 200) {
            for (Request r : requests) {
                Response resp = new Response();
                resp.error = 'Geocoder returned ' + res.getStatusCode();
                results.add(resp);
            }
            return results;
        }
        // Parse vendor batch response + map by accountId …
        return parseBatchResponse(res.getBody(), requests);
    }

    private static Map<String, Object> buildBatchPayload(List<Request> rs) {
        // implementation omitted
        return new Map<String, Object>();
    }
    private static List<Response> parseBatchResponse(String body, List<Request> rs) {
        // implementation omitted
        return new List<Response>();
    }
}
```

Because `callout=true`, the calling flow is forced to be invoked from a `Queueable` or from a Scheduled Path (no inline trigger context). The single batched HTTP call stays under the 100-callout limit regardless of bulk size.

**Why it works:** Vendor-batch endpoint means one HTTP call for N requests. `callout=true` flags the action for the Flow Builder and forces a correct async context.

---

## Example 3: Calling a Flow from Apex

**Context:** A scheduled Apex job needs to run the admin-maintained `Deactivate_Stale_Accounts` autolaunched flow without hard-coding the logic.

**Solution:**

```apex
public class StaleAccountJob implements Schedulable {
    public void execute(SchedulableContext sc) {
        Map<String, Object> inputs = new Map<String, Object>{
            'cutoffDate' => Date.today().addDays(-90)
        };
        Flow.Interview flow =
            Flow.Interview.createInterview('Deactivate_Stale_Accounts', inputs);
        flow.start();

        Integer deactivated =
            (Integer) flow.getVariableValue('deactivatedCount');
        System.debug('Deactivated: ' + deactivated);
    }
}
```

**Why it works:** Admin owns the flow logic; Apex owns the scheduling. The contract is the input/output variable names — flagged as "Available for Input / Output" in the flow.

---

## Anti-Pattern: Returning a shorter output list than the input list

**What practitioners do:** Skip records that don't match criteria by not adding anything to the output list.

**What goes wrong:** Flow's Loop element walks `inputs` and `outputs` in parallel assuming same length. Skipping records silently shifts every subsequent output onto the wrong input — downstream data corruption.

**Correct approach:** Always return exactly `inputs.size()` elements. For skipped records, add an empty response (with all fields null or an explicit `status = 'skipped'`).

---

## Anti-Pattern: Static caches leak across calls

**What practitioners do:** Cache lookup data in a static Map<String, Whatever> to avoid re-querying.

**What goes wrong:** Two flows running in the same transaction share the static map; changes from one leak into the other. Hard to debug because it only manifests under mixed load.

**Correct approach:** Build the lookup map as a local variable inside the invocable method. If genuine cross-call caching is needed, use `Platform Cache` with explicit partition + expiry.
