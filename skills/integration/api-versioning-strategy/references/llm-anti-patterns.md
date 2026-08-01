# LLM Anti-Patterns — API Versioning Strategy

Scope: versioning **your own** Apex REST endpoints. Consuming versioned Salesforce APIs
is a different problem. The thing assistants most often get wrong here is that Salesforce
exposes several independent version numbers, and only one of them is yours to control.

## Anti-Pattern 1: Assuming the platform versions your endpoint for you

Standard REST resources live under `/services/data/v64.0/...`, so assistants reason by
analogy that a custom endpoint gets the same treatment. It does not. Apex REST is served
from `/services/apexrest/` plus whatever you put in `urlMapping`, and the platform
contributes no version segment. If you do not put one there, your endpoint has no version
and never will without a breaking change.

**Wrong** — unversioned from day one; the first rename forces every consumer to move at
once:

```apex
@RestResource(urlMapping='/orders/*')
global with sharing class OrderApi {
    @HttpGet
    global static OrderDto doGet() {
        String id = RestContext.request.requestURI.substringAfterLast('/');
        return OrderService.toDto(OrderService.findById(id));
    }
}
```

**Right** — the version is a literal segment of your own mapping:

```apex
@RestResource(urlMapping='/v1/orders/*')
global with sharing class OrderApiV1 {
    @HttpGet
    global static OrderV1Dto doGet() {
        String id = RestContext.request.requestURI.substringAfterLast('/');
        return OrderV1Mapper.toDto(OrderService.findById(id));   // logic stays in the service
    }
}
```

Note that `urlMapping` must be unique across the org, which is precisely what makes
`/v1/` and `/v2/` able to coexist as separate classes.

Source: Apex REST — `@RestResource` and `urlMapping` —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest_intro.htm

## Anti-Pattern 2: Confusing your URL version with the class's own API version

Every Apex class carries an `apiVersion` in its `.cls-meta.xml`, and that number governs
which platform behaviour the class runs against — not what your consumers call. Assistants
conflate the two and either bump the metadata version to "release v2 of the API" or refuse
to bump it for fear of breaking consumers.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>64.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

❌ Leaving `OrderApiV1` pinned to an ancient `apiVersion` to "keep v1 stable".
✅ Keep the class's `apiVersion` current — it controls platform semantics your consumers
never see — and keep the contract stable through the `urlMapping` segment and the DTO
shape, which is the part they do see. These two numbers change on completely different
schedules and for completely different reasons.

## Anti-Pattern 3: Versioning for additive changes

Told "we added a field", assistants dutifully produce a v2. Adding an optional field to a
response is not breaking for any consumer that parses JSON by name, and a version bump
that carries no breaking change imposes a migration on everyone for nothing. Versions are
expensive: every live version is code you maintain, test and monitor.

Breaking, so version: renaming or removing a response field; changing a field's type;
tightening validation on a request; changing the error response shape; changing HTTP
status semantics.

Not breaking, so do not version: adding an optional response field; adding an optional
request field with a safe default; adding a new endpoint; relaxing validation.

❌ v2 because a nullable `deliveredAt` was added.
✅ Ship it into v1 and note it in the changelog. Consumers that ignore unknown fields —
which is the documented expectation you should publish — are unaffected.

## Anti-Pattern 4: Business logic inside the `@HttpGet` method

This is what makes versioning expensive later, and assistants produce it by default
because the shortest correct example puts everything in one method. When v2 arrives, the
logic has to be copied, and from then on every bug is fixed twice — or, more often, once.

❌ Query, transform, validate and serialise inside the resource class.
✅ The resource class does three things only: parse the request, call a service, map the
result to the DTO for its own version. `OrderApiV1` and `OrderApiV2` then differ only in
their mapper, which is the actual contract difference.

## Anti-Pattern 5: Announcing a sunset with no instrumentation behind it

The deprecation notice goes out, the ninety days pass, the endpoint is deleted, and a
consumer nobody knew about breaks. Assistants generate the `Sunset` header and treat the
job as done, because the header is the visible artefact.

**Wrong** — a header alone announces a date it cannot verify is safe:

```apex
@HttpGet
global static OrderV1Dto doGet() {
    RestContext.response.addHeader('Sunset', 'Wed, 31 Dec 2026 23:59:59 GMT');
    RestContext.response.addHeader('Deprecation', 'true');
    return OrderV1Mapper.toDto(OrderService.findById(orderIdFromUri()));
}
```

**Right** — announce and measure, then delete on evidence rather than on the calendar:

```apex
@HttpGet
global static OrderV1Dto doGet() {
    RestContext.response.addHeader('Deprecation', 'true');
    RestContext.response.addHeader('Sunset', 'Wed, 31 Dec 2026 23:59:59 GMT');
    RestContext.response.addHeader('Link', '</services/apexrest/v2/orders>; rel="successor-version"');

    // Attribution is the whole point: which consumer, not just how many calls.
    ApiUsageLogger.record('v1/orders', UserInfo.getUserId(),
        RestContext.request.headers.get('User-Agent'));

    String id = RestContext.request.requestURI.substringAfterLast('/');
    return OrderV1Mapper.toDto(OrderService.findById(id));
}
```

Delete when the log shows zero calls for a sustained period, not when the announced date
arrives. The date creates urgency; the log creates safety.

## Anti-Pattern 6: A version bump that silently changes error responses

Consumers branch on error shape as much as on success shape. Assistants redesign the
error envelope in v2 because it is "cleaner", and never list it as a breaking change
because no success field moved.

❌ v1 returns `{"message": "..."}`, v2 returns `{"errors":[{"code":"...","detail":"..."}]}`
with no migration note.
✅ Treat the error envelope as part of the contract, version it with everything else, and
document the mapping from old codes to new. An error path that changes shape without
notice fails at exactly the moment the consumer has the least capacity to cope.

## Anti-Pattern 7: Deleting the class instead of retiring the route

Removing the Apex class removes the endpoint abruptly, and a straggling consumer gets a
404 with no explanation. There is a cheaper intermediate step.

❌ Delete `OrderApiV1` on the sunset date.
✅ Replace its body with a `410 Gone` and a pointer to the successor for one more cycle,
then delete. The consumer gets a status that means "this is permanent, here is where it
went" rather than one that means "maybe you typed the URL wrong".
