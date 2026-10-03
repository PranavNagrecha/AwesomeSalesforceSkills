# Well-Architected Notes: Apex Wrapper Class Patterns

## Relevant Pillars

- **Performance Efficiency**: Wrapper classes aggregate data from multiple queries into a single heap structure, reducing round-trips between the client and server. Using `@AuraEnabled(cacheable=true)` on the returning method enables Lightning Data Service caching, reducing repeat server calls for static data. Keeping wrappers lean (only `@AuraEnabled` on fields the client actually needs) reduces JSON payload size over the wire.

- **Reliability**: Null-safe `compareTo()` and `compare()` implementations prevent null pointer exceptions during sorts on partially populated data. Top-level wrapper classes keep component contracts on supported ground (the LWC guide does not support inner classes as parameters or return values). `@JsonAccess` set only where another namespace needs it avoids runtime `JSONException` without widening access. Explicit sharing keywords on any class that touches data prevent unintended exposure.

## Architectural Tradeoffs

**Inner class vs top-level class:**
- Inner classes keep internal helpers (comparators, service-only value objects) next to the code that uses them.
- Top-level classes are required for any type passed to or returned from an `@AuraEnabled` method called by a Lightning web component or Aura component, and are the clean choice when several classes share the shape or it must be `global`.
- Keep the controller (static `@AuraEnabled` methods) and the wrapper (`@AuraEnabled` properties) in separate classes, as the Aura guide advises.

**Comparable vs Comparator:**
- `Comparable` is simpler (no extra class, one method) but locks in a single sort strategy. When business requirements change (e.g., "we now need to sort by two different fields"), the class must be modified.
- `Comparator<T>` isolates sort logic from the data class, so a new order is a new comparator and the wrapper stays unchanged. The cost is one more class per order. UNVERIFIED (2026-10-03): the API version that introduced `Comparator`.

**Heap usage:**
- Wrapper lists live entirely in heap memory. Very large lists of wrappers with many fields can approach the total heap limit: 6 MB synchronous, 12 MB asynchronous (Apex Developer Guide 262, Per-Transaction Apex Limits, pdftotext line 19577). For large datasets, return only the fields needed by the consumer and consider pagination rather than returning the full dataset.

## Anti-Patterns

1. **DML or SOQL inside wrapper constructors**: it runs once per instance, so limit consumption grows with list size, and an inner class without its own sharing keyword does not take the outer class's mode. Do data access in the controller or service and pass results to the constructor.

2. **Returning raw SObjects alongside a wrapper list**: Mixing raw `SObject` types and wrapper types in the same response forces the client to handle two different data shapes. Commit to one shape per method. If computed fields are needed, use a wrapper; if standard SObject fields suffice, return the SObject directly.

3. **Annotating all wrapper fields `@AuraEnabled` by default**: Over-annotating increases serialization payload and exposes fields the component does not use. Annotate only the minimum set of fields required by the LWC template. Fields containing sensitive data (e.g., SSN, internal cost) should never carry `@AuraEnabled`.

## Official Sources Used

- Apex Developer Guide, Summer '26 (262): "Inner classes" and "Using Static Methods and Variables" (no implicit outer-instance pointer, no statics), "Using the with sharing, without sharing, and inherited sharing Keywords" (Other Implementation Details, Versioned Behavior Changes for API 67.0), "AuraEnabled Annotation," "JsonAccess Annotation," "List Sorting," "Lists of Custom Types and Sorting," "Custom Sort Order of sObjects," "Per-Transaction Apex Limits" (heap, SOQL). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Reference Guide, Summer '26 (262): "Comparable Interface," "Comparator Interface." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf
- Lightning Aura Components Developer Guide, Summer '26 (262): "AuraEnabled Annotation," "Returning Data from an Apex Server-Side Controller," "Supported Apex Data Types," custom Apex class parameter example. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/lightning.pdf
- Lightning Web Components Developer Guide, "Expose Apex Methods to Lightning Web Components" (fetched 2026-10-03): https://developer.salesforce.com/docs/platform/lwc/guide/apex-expose-method.html
- Lightning Web Components Developer Guide, "Wire Apex Methods to Lightning Web Components" (fetched 2026-10-03): https://developer.salesforce.com/docs/platform/lwc/guide/apex-wire-method.html

### Earlier references kept from version 1.0.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Apex Developer Guide, Inner Classes (atlas page): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_understanding.htm
- Apex Reference Guide, Comparable Interface (atlas page): https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_comparable.htm
- Apex Reference Guide, Comparator Interface (atlas page): https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_Comparator.htm
- Apex Developer Guide, JsonAccess Annotation (atlas page): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_JsonAccess.htm
- Apex Developer Guide, AuraEnabled Annotation (atlas page): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_AuraEnabled.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (Well-Architected guide pages redirect to the home page)
