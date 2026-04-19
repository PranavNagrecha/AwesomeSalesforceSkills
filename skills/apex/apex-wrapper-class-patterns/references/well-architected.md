# Well-Architected Notes — Apex Wrapper Class Patterns

## Relevant Pillars

- **Performance Efficiency** — Wrapper classes aggregate data from multiple queries into a single heap structure, reducing round-trips between the client and server. Using `@AuraEnabled(cacheable=true)` on the returning method enables Lightning Data Service caching, reducing repeat server calls for static data. Keeping wrappers lean (only `@AuraEnabled` on fields the client actually needs) reduces JSON payload size over the wire.

- **Reliability** — Null-safe `compareTo()` and `compare()` implementations prevent `NullPointerException` during sort operations on partially populated datasets. Proper `@JsonAccess` annotation on REST-bound wrappers prevents silent runtime deserialization failures. Clear inner-class sharing semantics prevent unintended data exposure or access errors.

## Architectural Tradeoffs

**Inner class vs top-level class:**
- Inner classes keep related code co-located and prevent namespace pollution. They are appropriate when the wrapper is consumed only by its enclosing class.
- Top-level classes are required when (a) multiple unrelated classes share the wrapper shape, (b) the wrapper needs `@JsonAccess` for Apex REST (best practice is top-level for REST-facing types), or (c) the wrapper must be `global` for managed package consumption.
- Promoting too early creates unnecessary top-level class proliferation. Promoting too late creates duplication when a second consumer needs the same shape.

**Comparable vs Comparator:**
- `Comparable` is simpler — no extra class, one method, works at all API versions — but locks in a single sort strategy. When business requirements change (e.g., "we now need to sort by two different fields"), the class must be modified.
- `Comparator<T>` (API v60+) isolates sort logic from the data class, enabling the Open/Closed Principle — the wrapper class is open for extension (new comparators) without modification. The cost is an additional class per sort strategy.

**Heap usage:**
- Wrapper lists live entirely in heap memory. Very large lists (10 000+ elements) of wrappers with many fields can approach the 6 MB heap limit in synchronous contexts. For large datasets, return only the fields needed by the consumer and consider pagination rather than returning the full dataset.

## Anti-Patterns

1. **DML or SOQL inside wrapper constructors** — Issuing database operations inside a constructor is unpredictable: it fires once per instance, making governor limit consumption proportional to list size. It also executes in system mode (inner class context), bypassing sharing rules. Always perform data access in the outer service or controller method and pass results as constructor arguments.

2. **Returning raw SObjects alongside a wrapper list** — Mixing raw `SObject` types and wrapper types in the same response forces the client to handle two different data shapes. Commit to one shape per method. If computed fields are needed, use a wrapper; if standard SObject fields suffice, return the SObject directly.

3. **Annotating all wrapper fields `@AuraEnabled` by default** — Over-annotating increases serialization payload and exposes fields the component does not use. Annotate only the minimum set of fields required by the LWC template. Fields containing sensitive data (e.g., SSN, internal cost) should never carry `@AuraEnabled`.

## Official Sources Used

- Apex Developer Guide — Inner Classes: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_understanding.htm
- Apex Reference Guide — Comparable Interface: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_comparable.htm
- Apex Reference Guide — Comparator Interface: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_Comparator.htm
- Apex Developer Guide — JsonAccess Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_JsonAccess.htm
- Apex Developer Guide — AuraEnabled Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_AuraEnabled.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
