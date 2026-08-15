# Examples — Apex-Defined Types

Worked examples for modelling structured, non-sObject data that Flow can bind.

**The contract, stated once, because every example depends on it.** Salesforce's
considerations for the Apex-defined data type are unusually restrictive and
almost every draft written from Apex instincts violates one of them:

| Requirement | Detail |
|---|---|
| Field types | Boolean, Integer, Long, Decimal, Double, Date, DateTime, String — single values and lists of each |
| Annotation | `@AuraEnabled` on every field Flow must see |
| Constructor | A no-argument constructor is required |
| Inner classes | **Not supported** |
| Outer class named the same as an inner class | Not supported |
| Class methods | Not supported |
| Getter methods for fields | Not supported |
| List of lists as a field | Not supported |
| Referential integrity | Not supported — modify or delete a field in the class and the flow fails |

Two consequences that catch people: there is **no `Map`** on that type list, and
the "no inner classes" rule means a nested structure has to be built from
separate **top-level** classes, not from the nested-class shape every Apex
developer reaches for first.

---

## Example 1: Wrong vs Right — Nesting Without Inner Classes

**Context:** An HTTP Callout returns a weather payload with a nested daily
forecast array.

**Wrong:**

```apex
public class WeatherResponse {
    @AuraEnabled public String location;
    @AuraEnabled public Decimal temperatureC;
    @AuraEnabled public List<DailyForecast> forecast;

    // Inner class — NOT supported by the Apex-defined data type.
    public class DailyForecast {
        @AuraEnabled public Date day;
        @AuraEnabled public Decimal highC;
        @AuraEnabled public Decimal lowC;
    }
}
```

This is the idiomatic Apex shape for a nested DTO and it does not work here.
Inner classes are not supported, so `forecast` cannot be bound in Flow. Worse,
the class compiles and deploys perfectly — the failure appears only when someone
tries to reference the nested field from the flow, or does not appear at all
because the field is silently absent from the picker.

**Right — two top-level classes, two files:**

`DailyForecast.cls`

```apex
public class DailyForecast {
    @AuraEnabled public Date day;
    @AuraEnabled public Decimal highC;
    @AuraEnabled public Decimal lowC;

    public DailyForecast() {}
}
```

`WeatherResponse.cls`

```apex
public class WeatherResponse {
    @AuraEnabled public String location;
    @AuraEnabled public Decimal temperatureC;
    @AuraEnabled public String summary;
    @AuraEnabled public List<DailyForecast> forecast;

    public WeatherResponse() {}
}
```

**Why it works:** each class is top-level, every exposed field carries
`@AuraEnabled`, every field type is on the supported list (String, Decimal, Date,
and a `List<>` of another Apex-defined type), and both declare an explicit
no-argument constructor.

**Why declare the empty constructor explicitly** even though Apex supplies one
when you write none: a no-argument constructor is required, and the moment
someone adds a convenience constructor with arguments the implicit one
disappears. Writing it down makes the requirement visible at the point where it
would otherwise be silently removed. Add a comment saying why.

**Naming trap:** an outer class with the same name as an inner class is also not
supported. If `WeatherResponse` also contains a helper named `DailyForecast`
anywhere in the org's namespace, resolve the collision before wiring the flow.

---

## Example 2: There Is No Map — Model It as a List

**Context:** An external API returns an arbitrary bag of attributes.

**Wrong:**

```apex
public class ProductPayload {
    @AuraEnabled public String sku;
    @AuraEnabled public Map<String, String> attributes;   // Flow cannot bind this
}
```

`Map` is not on the supported type list. The field simply does not appear in
Flow, with no error to explain why.

**Right:**

`KeyValue.cls`

```apex
public class KeyValue {
    @AuraEnabled public String key;
    @AuraEnabled public String value;

    public KeyValue() {}
}
```

`ProductPayload.cls`

```apex
public class ProductPayload {
    @AuraEnabled public String sku;
    @AuraEnabled public List<KeyValue> attributes;

    public ProductPayload() {}
}
```

**Why it works:** a list of a supported Apex-defined type is supported, so Flow
can loop `attributes` and read `key` and `value` per iteration.

**What you have given up, and it is not nothing:** Flow has no map, so looking up
one key is a Loop with a Decision — O(n) per lookup, and inside a batched
record-triggered flow that multiplies by the interview batch size. If the flow
needs to look up three keys out of forty attributes, that is 120 iterations per
interview and 24,000 per full batch, against a 10,000 ms CPU budget shared with
everything else in the transaction.

When the flow only ever needs specific keys, **do not model the bag at all**.
Give the class the three named fields the flow actually consumes and let the Apex
that builds it do the map lookup once, in Apex, where a `Map` exists. That is the
version of this example most teams should have written.

---

## Example 3: An Invocable Returning a Typed Result

**Context:** Flow needs a pricing breakdown from a service that already exists in
Apex.

**Solution — three top-level classes:**

`PricingBreakdown.cls`

```apex
public class PricingBreakdown {
    @AuraEnabled public Decimal subtotal;
    @AuraEnabled public Decimal tax;
    @AuraEnabled public Decimal total;
    @AuraEnabled public String  currencyIsoCode;

    public PricingBreakdown() {}
}
```

`PriceQuoteRequest.cls`

```apex
public class PriceQuoteRequest {
    @InvocableVariable(required=true label='Quote Id')
    public Id quoteId;

    @InvocableVariable(label='Include Tax')
    public Boolean includeTax;
}
```

`PriceQuoteAction.cls`

```apex
public with sharing class PriceQuoteAction {

    @InvocableMethod(
        label='Quote Price'
        description='Returns a pricing breakdown for each supplied quote.'
        category='Pricing')
    public static List<PricingBreakdown> run(List<PriceQuoteRequest> requests) {
        List<PricingBreakdown> results = new List<PricingBreakdown>();
        // One query for the whole batch — never one per request.
        Map<Id, Quote> quotes = new Map<Id, Quote>([
            SELECT Id, Subtotal, TotalPrice
            FROM Quote
            WHERE Id IN :collectQuoteIds(requests)
        ]);
        for (PriceQuoteRequest req : requests) {
            results.add(buildBreakdown(quotes.get(req.quoteId), req.includeTax));
        }
        return results;
    }
    // ...
}
```

**Why the shape matters:** the invocable takes a `List<>` and returns a `List<>`
of the same length in the same order. That contract is what lets a flow call it
once with a collection instead of once per record inside a loop — and a
per-iteration invocable call is the most common way an Apex-backed flow ends up
slower than the pure-Flow version it replaced.

**`@InvocableVariable` is not `@AuraEnabled`.** The request class uses
`@InvocableVariable` because it is an invocable *input*; the return type uses
`@AuraEnabled` because Flow binds it as an Apex-defined variable. Mixing them up
produces a class that compiles and a flow that cannot see the fields.

---

## Example 4: Modelling Only What Flow Consumes

**Context:** An order-status API returns 60 fields. The flow displays four of
them and branches on a fifth.

**Problem:** Mirroring the upstream schema is the instinctive move — it feels
complete and future-proof. It is the opposite. Referential integrity is not
supported for Apex-defined class fields: if a field is modified or deleted in the
class, the flow fails. So every field you expose is a field you have committed
not to rename, and 60 fields is 60 commitments to support one screen.

**Solution:**

```apex
public class OrderStatusView {
    @AuraEnabled public String  orderNumber;
    @AuraEnabled public String  status;
    @AuraEnabled public Date    estimatedDelivery;
    @AuraEnabled public String  carrierName;
    @AuraEnabled public Boolean isDelayed;

    public OrderStatusView() {}
}
```

The Apex that calls the API parses the full 60-field payload — in Apex, where a
`Map<String, Object>` is available and cheap — and projects the five fields Flow
needs.

**Why it works:** the upstream schema can churn freely; the projection layer
absorbs it. Only a change to one of these five names is a breaking change to the
flow. It also names the class for its role (`OrderStatusView`) rather than its
source, which stops the next person assuming it must track the API one-for-one.

**Adding a field is safe. Removing or renaming one is not** — and it fails at
run time, in the flow, not at compile time in the class. Treat the field names as
a published interface with the same change process a subflow's input variables
get.

---

## Example 5: The Test That Catches the Real Failure

**Context:** A team wants a guard against the class drifting out of what Flow can
bind.

**Problem:** Every rule in the contract — `@AuraEnabled` on each field, a
no-argument constructor, no methods, no inner classes, supported types only —
can be broken by a change that compiles cleanly. There is no deploy-time gate.

**Solution:** a round-trip test plus an explicit shape assertion.

```apex
@IsTest
private class OrderStatusViewTest {

    @IsTest
    static void serializesAndDeserializesCleanly() {
        OrderStatusView v = new OrderStatusView();   // no-arg constructor must exist
        v.orderNumber       = 'SO-1001';
        v.status            = 'Shipped';
        v.estimatedDelivery = Date.newInstance(2026, 8, 20);
        v.carrierName       = 'Acme Freight';
        v.isDelayed         = false;

        String json = JSON.serialize(v);
        OrderStatusView back =
            (OrderStatusView) JSON.deserialize(json, OrderStatusView.class);

        System.assertEquals('SO-1001', back.orderNumber);
        System.assertEquals(Date.newInstance(2026, 8, 20), back.estimatedDelivery);
        System.assertEquals(false, back.isDelayed);
    }

    @IsTest
    static void everyFieldIsFlowVisible() {
        // Guards the contract: any field added without @AuraEnabled, or of an
        // unsupported type, changes this count or this set and fails here
        // rather than silently disappearing from Flow.
        Set<String> expected = new Set<String>{
            'orderNumber', 'status', 'estimatedDelivery', 'carrierName', 'isDelayed'
        };
        Map<String, Object> actual = (Map<String, Object>)
            JSON.deserializeUntyped(JSON.serialize(new OrderStatusView()));
        System.assertEquals(expected, actual.keySet(),
            'Field set changed. Every Flow referencing this class must be reviewed.');
    }
}
```

**Why it works:** the first test proves the class is JSON round-trippable and
that the no-argument constructor exists. The second turns "somebody renamed a
field" from a run-time flow failure into a failed build, which is the only place
this class of change can be caught cheaply.

**What the test does not catch:** `JSON.serialize` happily emits fields without
`@AuraEnabled`, so the second test guards the *names* but not the annotation.
Pair it with a code review rule, or a static check over the class source, if the
annotation has been dropped before.

---

## Anti-Pattern: Putting Behaviour on the Type

**What practitioners do:** Add a `calculateTotal()` method, a static factory, or
a getter to the Apex-defined class — normal, good object-oriented design.

**What goes wrong:** class methods are not supported, and getter methods for
fields are not supported. The class still compiles, so the failure surfaces as
Flow behaving oddly around that type rather than as anything that names the
cause.

**Correct approach:** keep the type data-only, with public fields and a
no-argument constructor. Behaviour lives in the service that produces or consumes
it. A useful shorthand: if it would be a `record` or a plain struct in another
language, it is the right shape here.

---

## Anti-Pattern: A Constructor With Required Arguments

**What practitioners do:** Add `public OrderStatusView(String orderNumber,
String status)` for convenience in the Apex that builds it.

**What goes wrong:** adding any constructor removes the implicit no-argument one,
and a no-argument constructor is required. Flow does not call constructors with
arguments, so the type stops being buildable from Flow.

**Correct approach:** if you want a convenience constructor, declare the
no-argument one explicitly alongside it. Better: leave the class bare and do the
population in a factory method on a *different* class, which keeps the type clean
and the convenience where behaviour is allowed.

---

## Anti-Pattern: Renaming a Field and Trusting the Compiler

**What practitioners do:** Rename `estimatedDelivery` to `promisedDate` across
the codebase, compile, deploy.

**What goes wrong:** referential integrity is not supported for Apex-defined class
fields. Flow binds by field name at run time, so the compiler sees nothing wrong
and the flow fails when it next runs. If the flow is scheduled or
record-triggered, that is the next batch — with no user present.

**Correct approach:** treat the field names as a published interface. Search
every flow for references to the class before renaming, and treat the rename as a
breaking change with a caller inventory, exactly as `flow/flow-versioning-strategy`
treats a flow's own input variables. The build-time shape assertion in Example 5
is the cheapest available guard.
