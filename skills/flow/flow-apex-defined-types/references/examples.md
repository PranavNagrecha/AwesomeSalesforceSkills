# Examples — Apex-Defined Types

## Example 1: HTTP Callout Response

```apex
public class WeatherResponse {
    @AuraEnabled public String location;
    @AuraEnabled public Decimal temperatureC;
    @AuraEnabled public String summary;
    @AuraEnabled public List<DailyForecast> forecast;
}

public class DailyForecast {
    @AuraEnabled public Date day;
    @AuraEnabled public Decimal highC;
    @AuraEnabled public Decimal lowC;
}
```

Flow binds `WeatherResponse.forecast` as a collection of `DailyForecast`
and can loop it.

## Example 2: Invocable Return

```apex
public class PricingBreakdown {
    @AuraEnabled public Decimal subtotal;
    @AuraEnabled public Decimal tax;
    @AuraEnabled public Decimal total;
}

public class PriceQuoteAction {
    @InvocableMethod(label='Quote Price')
    public static List<PricingBreakdown> run(List<Request> reqs) { ... }
}
```

## Example 3: Replacing A Map

Bad (does not work in Flow):

```apex
@AuraEnabled public Map<String, String> attributes;
```

Good:

```apex
@AuraEnabled public List<KeyValue> attributes;

public class KeyValue {
    @AuraEnabled public String key;
    @AuraEnabled public String value;
}
```
