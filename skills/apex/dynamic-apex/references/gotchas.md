# Gotchas — Dynamic Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Schema.getGlobalDescribe() Cost Compounds in Batch and Trigger Contexts

**What happens:** `Schema.getGlobalDescribe()` retrieves metadata for every accessible sObject in the org. In large orgs this can be several hundred objects. Calling it more than once per transaction wastes CPU time and can contribute to hitting the 10-second CPU limit in heavy batch jobs or trigger handlers that process large volumes.

**When it occurs:** Any time `getGlobalDescribe()` is called inside a loop, in a helper method without a static cache, or in a class that is instantiated multiple times. Often appears in refactored code where describe calls were originally top-level but got moved inside iteration logic during a feature addition.

**How to avoid:** Declare a `private static final Map<String, Schema.SObjectType> GLOBAL_DESCRIBE = Schema.getGlobalDescribe();` at the class level. The JVM populates this once when the class is first loaded in the transaction. All subsequent reads hit the in-memory map. Apply the same pattern to per-object field maps using a second static `Map<String, Map<String, Schema.SObjectField>>` cache populated lazily on first access per object.

---

## Gotcha 2: Field Set Members Can Reference Deleted Fields

**What happens:** Salesforce does not automatically remove a deleted field from any Field Set that references it. `Schema.FieldSet.getFields()` continues to return the deleted field's `FieldSetMember`, but looking up that field name in the object's live field map returns `null`. Building a query that includes the deleted field name causes a `QueryException` at runtime.

**When it occurs:** Any deployment that deletes a custom field without auditing Field Set membership. This is common after data model clean-ups or package upgrades that deprecate fields.

**How to avoid:** Always validate Field Set members against the live `DescribeSObjectResult.fields.getMap()` before including them in a query string. If a member name is absent from the field map, either skip it silently (with logging) or throw a descriptive error. Never blindly join Field Set member paths into SELECT clauses.

---

## Gotcha 3: String.escapeSingleQuotes() Does Not Protect Object and Field Names

**What happens:** Developers apply `String.escapeSingleQuotes()` to field or object names that come from configuration or user input, assuming this makes them safe to concatenate. The function only escapes the `'` character (single quote). It does not block injections that use unquoted SOQL structure — for example, injecting `Name LIMIT 1 --` as a "field name" or injecting `1=1` as a numeric filter value without quotes.

**When it occurs:** Field and object names are fundamentally different from string literal values in SOQL. String literals go inside quotes in the query; field and object names are unquoted identifiers. `escapeSingleQuotes()` only helps with quoted strings. Using it on an object or field name gives a false sense of security.

**How to avoid:** Allowlist object names by checking `Schema.getGlobalDescribe().containsKey(name)`. Allowlist field names by checking `DescribeSObjectResult.fields.getMap().containsKey(name)`. Reject any name that does not appear in the describe result. Use bind variables or `escapeSingleQuotes()` only for filter values that appear inside string delimiters in the query.

---

## Gotcha 4: record.put() Does Not Throw on Type Mismatch Until DML

**What happens:** Calling `record.put('CurrencyField__c', 'not-a-number')` does not immediately throw a `SObjectException`. The runtime accepts the call and the error surfaces at the DML statement as a `System.TypeException` or `DmlException`, making the root cause difficult to trace in stack traces.

**When it occurs:** Dynamic field assignment where the field type is inferred from a configuration map or external system value. A field that was a Number in a previous version is now a Text field, or a Currency field receives a String representation of a number.

**How to avoid:** Before calling `put()` with a dynamically typed value, inspect `DescribeFieldResult.getType()` to confirm the field type matches the value type. For numeric fields, cast to `Decimal` explicitly. For date fields, use `Date.valueOf()` or `DateTime.valueOf()`. For booleans, check the schema type and convert from String if necessary. Test these paths with both correct and incorrect value types in unit tests.

---

## Gotcha 5: WITH SECURITY_ENFORCED Throws, It Does Not Filter

**What happens:** Developers add `WITH SECURITY_ENFORCED` to a dynamic SOQL string expecting inaccessible fields to be silently omitted from results. Instead, if the running user lacks access to any field in the SELECT clause, the platform throws a `QueryException` at runtime, not a graceful degradation.

**When it occurs:** Used in user-facing utilities where the intent was to "return what the user can see" rather than "fail if the user cannot see everything." The exception terminates the transaction unless caught, making the utility entirely unavailable to users with restricted profiles rather than partially functional.

**How to avoid:** For graceful degradation, pre-filter the SELECT field list using `DescribeFieldResult.isAccessible()` before building the query string — exclude inaccessible fields rather than relying on `WITH SECURITY_ENFORCED` to handle them. Reserve `WITH SECURITY_ENFORCED` for contexts where any inaccessible field is a programming error and failure is the correct behavior.
