# Well-Architected — Apex-Defined Types

## Relevant Pillars

- **Reliability** — every constraint on this type fails at run time in the flow
  rather than at compile time in the class. A missing `@AuraEnabled`, an inner
  class, an added constructor, a renamed field: all compile, all deploy, all
  break the flow later. That asymmetry is the defining property of the domain and
  the reason a build-time shape assertion is worth writing.
- **Operational Excellence** — a tight, documented class with a named role is
  auditable; a 60-field mirror of an upstream API is a maintenance liability
  dressed as completeness, because referential integrity is unsupported and every
  field is a commitment.
- **Adaptable** — the projection layer is the whole value. Parse the upstream
  payload in Apex, where `Map<String, Object>` is free, and expose only what Flow
  consumes. Upstream churn then stops at the class boundary instead of reaching
  the flow.

## Architectural Tradeoffs

- **Apex-defined type vs JSON string:** the class is strict, readable, and
  bindable in the Flow picker; a JSON string carried as text is flexible and
  pushes all parsing and validation onto whoever consumes it. Use the class when
  the shape is stable enough to be worth a contract, and the string when it
  genuinely changes faster than a deploy cycle.
- **Named fields vs a `List<KeyValue>` bag:** named fields are a contract with
  referential-integrity risk on rename; the bag survives upstream additions and
  costs an O(n) Loop-and-Decision per lookup in Flow, multiplied by the interview
  batch size. Prefer named fields for the keys the flow actually reads, and
  resolve the bag in Apex where a `Map` exists.
- **Shared type vs per-flow type:** a shared type removes duplication and couples
  every consuming flow to one field-name change. Split rather than adding
  optional fields when two consumers diverge — an optional field is a permanent
  commitment for a temporary convenience.
- **Modelling the whole schema vs projecting:** the mirror is faster to write once
  and costs a caller inventory on every upstream change. The projection costs a
  mapping layer and confines churn to Apex.
- **Rich collections in a screen flow vs identifiers:** carrying full structures
  across screens is simple and pays heap on every transition, and pause storage on
  every pause. Carrying Ids and re-fetching is more work and more correct for
  anything another user can edit.

## Hygiene

- Every type Flow touches is a top-level class in its own file. No inner classes.
- Every exposed field carries `@AuraEnabled`.
- Every class declares `public MyType() {}` explicitly, with a comment saying it
  is required.
- No methods, no getters, no `Map`, no list of lists as a field.
- Field types come only from Boolean, Integer, Long, Decimal, Double, Date,
  DateTime, String, and lists of those or of other supported Apex-defined types.
- Every class has a test that JSON round-trips an instance **and** asserts the
  serialized field-name set, so a rename fails the build rather than the next
  scheduled batch.
- Invocable methods take and return `List<>`.
- A field rename carries a flow-caller inventory.

## Related

- `flow/flow-http-callout-action` — the most common producer of these types.
- `flow/flow-external-services` — External Services schemas and their generated
  types.
- `flow/flow-invocable-from-apex` — the invocable contract and the `List<>` shape
  that keeps it bulk-safe.
- `flow/flow-batch-processing-alternatives` — why a per-iteration invocable call
  costs so much.
- `flow/flow-versioning-strategy` — the caller-inventory discipline a field
  rename needs.
- `apex/apex-invocable-methods` — the Apex side of the boundary.

## Official Sources Used

- Considerations for the Apex-Defined Data Type — supported data types are Boolean, Integer, Long, Decimal, Double, Date, DateTime, and String, with single values and lists of each; the `@AuraEnabled` annotation for each field is required; a constructor with no arguments is required; class methods, getter methods for fields, and inner classes are not supported; an outer class with the same name as an inner class is not supported; a flow doesn't support a list-of-lists data type as a field on an Apex-defined flow variable; referential integrity is not supported for Apex class fields, and if the field is modified or deleted in the class the flow fails — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_apex_data_type.htm&type=5
- Apex-Defined Data Type — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_apex_type.htm&type=5
- Extend Flows with the Apex-Defined Data Type — https://help.salesforce.com/s/articleView?id=sf.flow_build_extend_apex_type.htm&type=5
- AuraEnabled Annotation (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_AuraEnabled.htm
- Supported Data Types in Flows (Lightning Web Components Developer Guide) — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-data-types.html
- Per-Transaction Apex Governor Limits — the 6 MB / 12 MB heap ceiling a large Apex-defined collection is charged against — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
