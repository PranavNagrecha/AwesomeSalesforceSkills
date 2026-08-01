# Examples — API Versioning Strategy

## Example 1: A v1/v2 pair sharing one service layer

**Context:** `/services/apexrest/v1/orders` returns `customerId`. The field actually holds
an Account Id, and the naming has caused three integration defects, so it is being renamed
to `accountId`.

**Problem:** renaming a response field is breaking. Four external consumers read
`customerId`, and they cannot all deploy on the same day. The endpoint has to serve both
shapes at once.

**Solution:** two thin resource classes, two mappers, one service. The only thing that
differs between versions is the mapper.

**v1** — frozen contract, with deprecation and sunset advertised and usage attributed:

```apex
@RestResource(urlMapping='/v1/orders/*')
global with sharing class OrderApiV1 {

    @HttpGet
    global static Map<String, Object> doGet() {
        RestContext.response.addHeader('Deprecation', 'true');
        RestContext.response.addHeader('Sunset', 'Wed, 31 Dec 2026 23:59:59 GMT');
        RestContext.response.addHeader(
            'Link', '</services/apexrest/v2/orders>; rel="successor-version"');
        ApiUsageLogger.record('v1/orders', UserInfo.getUserId(),
            RestContext.request.headers.get('User-Agent'));

        Order o = OrderService.findById(orderIdFromUri());
        return new Map<String, Object>{
            'orderId'    => o.Id,
            'customerId' => o.AccountId,          // the old, misleading name
            'total'      => o.TotalAmount,
            'status'     => o.Status
        };
    }

    private static Id orderIdFromUri() {
        return (Id) RestContext.request.requestURI.substringAfterLast('/');
    }
}
```

**v2** — corrected contract; the same service call with a different projection:

```apex
@RestResource(urlMapping='/v2/orders/*')
global with sharing class OrderApiV2 {

    @HttpGet
    global static Map<String, Object> doGet() {
        Order o = OrderService.findById(
            (Id) RestContext.request.requestURI.substringAfterLast('/'));
        return new Map<String, Object>{
            'orderId'   => o.Id,
            'accountId' => o.AccountId,           // renamed
            'total'     => o.TotalAmount,
            'status'    => o.Status,
            'placedAt'  => o.EffectiveDate        // additive; safe to backport to v1 too
        };
    }
}
```

**Why it works:** `urlMapping` must be unique across the org, so `/v1/orders/*` and
`/v2/orders/*` coexist as two independent routes with no dispatcher to write. Because
`OrderService.findById` is shared, a bug fixed in the query is fixed for both versions —
which is the failure mode you are buying protection against, since the alternative is a
copied class where the fix lands in one version and not the other. Note that `placedAt`
is additive and could be added to v1 as well: a consumer that ignores unknown fields is
unaffected, and there is no reason to make people migrate for a new field.

---

## Example 2: Sunsetting v1 on evidence

**Context:** v1 has been deprecated for ninety days. The announced sunset date has
arrived.

**Problem:** the team knows how many calls v1 received in total, but not who made them.
Deleting the class on the strength of a declining total is how a quarterly batch job that
runs on the 1st gets discovered on the 1st.

**Solution:** attribute, then retire in two steps.

```apex
public with sharing class ApiUsageLogger {

    /** Fire-and-forget so a logging failure can never fail the API call itself. */
    public static void record(String route, Id callerId, String userAgent) {
        EventBus.publish(new Api_Call__e(
            Route__c      = route,
            Caller_User__c = callerId,
            User_Agent__c = userAgent == null ? 'unknown' : userAgent.left(255),
            Called_At__c  = System.now()));
    }
}
```

The retirement query — the number that actually authorises deletion is the count of
*distinct callers*, over a window long enough to include the slowest scheduled consumer:

```sql
SELECT Caller_User__c, COUNT(Id) calls, MAX(Called_At__c) lastSeen
FROM Api_Call_Log__c
WHERE Route__c = 'v1/orders' AND Called_At__c = LAST_N_DAYS:45
GROUP BY Caller_User__c
ORDER BY MAX(Called_At__c) DESC
```

**Retire in two steps rather than one:**

1. On the sunset date, replace the v1 body with a `410 Gone` that names the successor.
   A consumer that appears late gets a status meaning "this is permanent and here is
   where it went", rather than a `404` that reads like a typo. Keep logging.
2. Delete the class only after the log shows zero distinct callers across a window that
   spans your longest consumer cadence — 45 days catches a monthly job, and a quarterly
   job needs a quarter.

```apex
@RestResource(urlMapping='/v1/orders/*')
global with sharing class OrderApiV1 {
    @HttpGet
    global static Map<String, Object> doGet() {
        ApiUsageLogger.record('v1/orders-gone', UserInfo.getUserId(),
            RestContext.request.headers.get('User-Agent'));
        RestContext.response.statusCode = 410;
        RestContext.response.addHeader(
            'Link', '</services/apexrest/v2/orders>; rel="successor-version"');
        return new Map<String, Object>{
            'errorCode' => 'GONE',
            'message'   => 'v1/orders was retired. Use /services/apexrest/v2/orders.'
        };
    }
}
```

**Why it works:** the announced date creates the urgency that gets consumers to migrate;
the distinct-caller log creates the evidence that makes deletion safe. Those are two
different jobs and a calendar cannot do the second one. The `410` step costs one release
and converts the worst-case outcome from "an unknown consumer breaks silently" into "an
unknown consumer receives a precise, logged instruction".
