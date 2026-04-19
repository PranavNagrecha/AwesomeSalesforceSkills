# Well-Architected Notes — Apex JSON Serialization

## Relevant Pillars

- **Performance Efficiency** — JSON payloads contribute to heap consumption (6 MB sync / 12 MB async). Large payloads should use streaming `JSONGenerator`/`JSONParser` rather than loading the full object graph into memory. Null suppression via `suppressApexObjectNulls` reduces payload size and downstream parsing overhead.
- **Reliability** — Deserializing external JSON without catching `TypeException` and `JSONException` creates unhandled exceptions that abort transactions and can trigger duplicate processing on retry. All external deserialization must be wrapped in error handling.
- **Security** — Avoid logging raw JSON payloads that may contain PII or credentials. Mask sensitive fields before serializing for audit trails.
- **Operational Excellence** — Use structured error payloads (error code + message) rather than raw exception stack traces in API error responses.

## Architectural Tradeoffs

**Typed vs. untyped deserialization:** `JSON.deserialize` into a typed class is safer and more readable but breaks on shape changes. `JSON.deserializeUntyped` is more resilient to schema drift but loses compile-time safety and requires explicit casting throughout. For internal Salesforce-to-Salesforce payloads (where schema is controlled), prefer typed. For third-party APIs (where schema can change independently), consider a hybrid approach: typed outer wrapper with `Map<String,Object>` for flexible inner structures.

**JSON.serialize vs. JSONGenerator:** `JSON.serialize` covers most cases with less code. `JSONGenerator` is warranted only when field ordering matters (some APIs are order-sensitive), payload size exceeds ~500 KB, or you need to interleave JSON construction with streaming logic.

## Anti-Patterns

1. **Unguarded `JSON.deserialize` on external data** — calling `JSON.deserialize` without catching `TypeException` treats external API contracts as immutable. Any type change in the external schema causes an uncaught exception that rolls back the transaction and may trigger duplicate processing if the caller retries.
2. **Serializing static or transient fields** — placing data in static fields and expecting it to appear in `JSON.serialize` output silently omits the data. This is especially common when migrating Java POJO patterns to Apex.
3. **Ignoring heap cost of large payloads** — deserializing multi-MB JSON responses in a sync context risks `System.LimitException: Apex heap size too large`, which is uncatchable and terminates the transaction.

## Official Sources Used

- Apex Developer Guide — JSON Support: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_json_overview.htm
- Apex Reference Guide — JSON Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Json.htm
- Apex Reference Guide — JSONGenerator: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_JSONGenerator.htm
- Apex Reference Guide — JSONParser: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_JSONParser.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
