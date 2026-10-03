# Gotchas: Apex Wrapper Class Patterns

Non-obvious Apex and component-framework behaviors that cause real production problems with wrapper classes. Each one names the official source it rests on.

## Gotcha 1: Inner classes as component parameters or return values are unsupported

**What happens:** A controller returns `List<Controller.Row>` to a Lightning web component. It may work in some orgs and fail in others, and Salesforce does not support it.

**When it occurs:** When the wrapper is declared as an inner class of the controller, which most tutorials show.

**How to avoid:** Declare component-facing wrappers as top-level classes. Do not use inheritance in classes used as component attributes either.

**Source:** Lightning Web Components Developer Guide, "Expose Apex Methods to Lightning Web Components": "An Apex inner class as a parameter or return value for an Apex method that's called by a Lightning web component isn't supported." Lightning Aura Components Developer Guide (262): custom Apex classes used for component attributes "can't be inner classes or use inheritance ... their use is unsupported in all cases"; with Lightning Web Security enabled, an inner class can't be a parameter or return value.

---

## Gotcha 2: Unannotated properties never reach the client

**What happens:** The component receives objects whose properties are `undefined`.

**When it occurs:** When `@AuraEnabled` is on the method but not on the wrapper's properties, or a new property is added without it.

**How to avoid:** Annotate every public property the template reads. Leave server-only properties unannotated.

**Source:** Lightning Aura Components Developer Guide (262), "Returning Data from an Apex Server-Side Controller": "Only the values of public instance properties and methods annotated with @AuraEnabled are serialized and returned."

---

## Gotcha 3: Parameters need getters and setters

**What happens:** A wrapper sent from the component back to Apex arrives with null properties.

**When it occurs:** When the wrapper is used as an `@AuraEnabled` method parameter and its properties are plain fields.

**How to avoid:** Declare parameter properties as `@AuraEnabled public String name { get; set; }`.

**Source:** Lightning Aura Components Developer Guide (262), custom Apex class parameter example: "Each property in the Apex class must have an @AuraEnabled annotation, as well as a getter and setter."

---

## Gotcha 4: Mixing controller methods and wrapper properties in one class

**What happens:** A single class holds both static `@AuraEnabled` methods and `@AuraEnabled` instance properties, a combination the Aura guide tells you to avoid.

**When it occurs:** When a controller also acts as its own return type.

**How to avoid:** Keep the controller and the wrapper in separate top-level classes.

**Source:** Lightning Aura Components Developer Guide (262), "AuraEnabled Annotation": "Don't mix-and-match these different uses of @AuraEnabled in the same Apex class."

---

## Gotcha 5: compareTo() and compare() must handle nulls

**What happens:** `List.sort()` throws a null pointer exception on a list with a null element or a wrapper whose sort key is null.

**When it occurs:** On real data where optional fields (for example `Opportunity.Amount`) are blank.

**How to avoid:** Check both arguments and the key fields for null and pick a rule (nulls first or last).

**Source:** Apex Reference Guide (262), "Comparable Interface" and "Comparator Interface": "Your implementation must explicitly handle null inputs ... to avoid a null pointer exception."

---

## Gotcha 6: Inner classes don't inherit the outer class's sharing mode

**What happens:** An inner class that runs SOQL behaves differently from the `with sharing` outer class around it.

**When it occurs:** When a wrapper constructor or helper method queries records.

**How to avoid:** Keep queries in the controller or service. If an inner class must query, give it an explicit sharing keyword. In API 67.0 and later, a class without a declaration runs with sharing; in 66.0 and earlier, a non-entry-point class without one takes its caller's mode.

**Source:** Apex Developer Guide (262), "Using the with sharing, without sharing, and inherited sharing Keywords," Other Implementation Details and Versioned Behavior Changes.

---

## Gotcha 7: @JsonAccess is about namespaces, not about REST

**What happens:** Teams add `@JsonAccess(serializable='always' deserializable='always')` to every REST wrapper, widening access to all namespaces when nothing needed it. Or code in another namespace fails to deserialize a class with `JSONException`.

**When it occurs:** When the annotation is treated as a REST requirement.

**How to avoid:** Leave it off for same-namespace code; since API 49.0 the default for both directions is `sameNamespace`. Add the narrowest value that the cross-namespace case needs. Subclasses don't inherit it.

**Source:** Apex Developer Guide (262), "JsonAccess Annotation," JsonAccess Considerations and Versioned Behavior Changes.

---

## Gotcha 8: Collator sorting changes with the running user

**What happens:** A list sorted with `Collator` comes back in a different order for users with different locales.

**When it occurs:** In triggers or code whose output order other logic depends on.

**How to avoid:** Use `Collator` only for display ordering. Avoid it in triggers and in code that expects a fixed order.

**Source:** Apex Developer Guide (262), "Lists of Custom Types and Sorting."
