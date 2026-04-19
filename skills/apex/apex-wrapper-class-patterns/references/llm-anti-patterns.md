# LLM Anti-Patterns — Apex Wrapper Class Patterns

Common mistakes AI coding assistants make when generating or advising on Apex wrapper and inner class patterns. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: compareTo() Without Null Guard

**What the LLM generates:**

```apex
public Integer compareTo(Object compareTo) {
    MyWrapper other = (MyWrapper) compareTo;
    return this.amount > other.amount ? 1 : (this.amount < other.amount ? -1 : 0);
}
```

**Why it happens:** LLMs are trained on Java and generic sorting examples where null inputs to `compareTo` are considered a contract violation. In Apex, `List.sort()` can pass null internally when the list contains null-field wrappers, and the Apex runtime does not enforce the no-null precondition that Java's `Comparable` contract implies.

**Correct pattern:**

```apex
public Integer compareTo(Object compareTo) {
    if (compareTo == null) return 1;
    MyWrapper other = (MyWrapper) compareTo;
    Decimal thisAmt  = this.amount  == null ? Decimal.valueOf(-1) : this.amount;
    Decimal otherAmt = other.amount == null ? Decimal.valueOf(-1) : other.amount;
    if (thisAmt > otherAmt) return 1;
    if (thisAmt < otherAmt) return -1;
    return 0;
}
```

**Detection hint:** Look for `compareTo` implementations that cast the argument and immediately dereference a field without a prior null check. Any pattern matching `(MyClass) compareTo\.\w+` without a preceding `if (compareTo == null)` is suspect.

---

## Anti-Pattern 2: Assuming Inner Class Inherits Outer Class Sharing

**What the LLM generates:**

```apex
public with sharing class MyService {
    public class MyWrapper {
        public List<Account> getVisibleAccounts() {
            // LLM assumes this respects the outer class's with sharing declaration
            return [SELECT Id, Name FROM Account];
        }
    }
}
```

**Why it happens:** The LLM extrapolates from Java's inner-class behavior (where inner classes inherit enclosing class access modifiers) to Apex. In Apex, inner classes do not inherit the `with sharing` / `without sharing` context — they execute in system mode for any data operations they independently perform.

**Correct pattern:**

```apex
public with sharing class MyService {
    // Perform SOQL in outer class where with sharing is enforced
    @AuraEnabled(cacheable=true)
    public static List<MyWrapper> getRows() {
        List<Account> accts = [SELECT Id, Name FROM Account]; // respects sharing
        List<MyWrapper> rows = new List<MyWrapper>();
        for (Account a : accts) {
            rows.add(new MyWrapper(a)); // wrapper just holds the data
        }
        return rows;
    }

    public class MyWrapper {
        @AuraEnabled public Id accountId;
        @AuraEnabled public String name;
        public MyWrapper(Account a) {
            this.accountId = a.Id;
            this.name = a.Name;
        }
        // NO SOQL inside the inner class
    }
}
```

**Detection hint:** Any SOQL or DML statement inside an inner class method or constructor should be flagged for review, especially if the outer class is declared `with sharing`.

---

## Anti-Pattern 3: Forgetting @AuraEnabled on Wrapper Fields

**What the LLM generates:**

```apex
public class AccountRow {
    public Id accountId;
    public String accountName;
    public Integer openOpportunityCount;
}

@AuraEnabled(cacheable=true)
public static List<AccountRow> getRows() { ... }
```

**Why it happens:** LLMs see the `@AuraEnabled` on the method and assume that is sufficient for the entire return type to be serialized and accessible in LWC. The annotation requirement on individual fields is a Salesforce-specific behavior not present in general Java or REST API patterns.

**Correct pattern:**

```apex
public class AccountRow {
    @AuraEnabled public Id accountId;
    @AuraEnabled public String accountName;
    @AuraEnabled public Integer openOpportunityCount;
}
```

**Detection hint:** Any wrapper class returned by an `@AuraEnabled` method where the wrapper fields lack `@AuraEnabled` themselves. Search for `@AuraEnabled` on methods and then verify the return type's fields also carry the annotation.

---

## Anti-Pattern 4: Using @JsonAccess Incorrectly for REST Deserialization

**What the LLM generates — variant A (missing annotation entirely):**

```apex
public class MyRequestBody {
    public String externalId;
    public Decimal value;
}
```

Used inside a `@RestResource` endpoint. Fails at runtime with `System.JSONException: Type is not visible`.

**What the LLM generates — variant B (annotation on inner class):**

```apex
public class MyController {
    @JsonAccess(serializable='always' deserializable='always')
    public class MyRequestBody { ... } // @JsonAccess does not work on inner classes for REST
}
```

**Why it happens:** LLMs either omit the annotation entirely (unfamiliar with the Salesforce-specific requirement) or apply it to an inner class, which does not satisfy the REST deserializer's requirement for a top-level accessible type.

**Correct pattern:**

```apex
// Top-level class, not inner
@JsonAccess(serializable='always' deserializable='always')
public class MyRequestBody {
    public String externalId;
    public Decimal value;
}
```

**Detection hint:** Any class used as a parameter type or deserialization target in a `@RestResource` method that lacks `@JsonAccess` at the class level, or that is declared as an inner class.

---

## Anti-Pattern 5: Using Comparator When the Org Is Below API v60

**What the LLM generates:**

```apex
// Saved at API version 58.0
public class PriceAscComparator implements Comparator<ProductWrapper> {
    public Integer compare(ProductWrapper o1, ProductWrapper o2) { ... }
}
```

**Why it happens:** The LLM recommends `Comparator<T>` as a modern best practice (which it is) without checking the class's API version. `Comparator` was introduced in Spring '24 (API v60.0) and is unavailable in classes saved at lower versions.

**Correct pattern:** Before recommending `Comparator<T>`, confirm the target class is saved at API v60.0 or higher. If not, use `Comparable` with a sort-direction flag pattern, or update the class API version first.

```apex
// API version must be 60.0+ in the class file header
// In Metadata API: <apiVersion>60.0</apiVersion> in the .cls-meta.xml file
public class PriceAscComparator implements Comparator<ProductWrapper> {
    public Integer compare(ProductWrapper o1, ProductWrapper o2) {
        Decimal p1 = o1.price == null ? 0 : o1.price;
        Decimal p2 = o2.price == null ? 0 : o2.price;
        if (p1 < p2) return -1;
        if (p1 > p2) return 1;
        return 0;
    }
}
```

**Detection hint:** `implements Comparator` in a class whose `.cls-meta.xml` `<apiVersion>` is below `60.0`. Also flag any `List.sort(new SomeComparator())` call in a class saved at a lower version.

---

## Anti-Pattern 6: DML or SOQL Inside Wrapper Constructor

**What the LLM generates:**

```apex
public class CaseWrapper {
    public Case theCase;
    public List<CaseComment> comments;

    public CaseWrapper(Id caseId) {
        this.theCase = [SELECT Id, Subject FROM Case WHERE Id = :caseId];
        this.comments = [SELECT Id, CommentBody FROM CaseComment WHERE ParentId = :caseId];
    }
}
```

**Why it happens:** LLMs model wrapper constructors like service constructors — a place to fetch data for the object. In Apex, issuing SOQL inside a constructor called in a loop (e.g., `new CaseWrapper(id)` for each of 200 Cases) fires one SOQL query per constructor call, hitting the 100 SOQL per transaction limit instantly.

**Correct pattern:** Perform all SOQL in bulk outside the constructor. Pass pre-fetched data in:

```apex
public class CaseWrapper {
    @AuraEnabled public Case theCase;
    @AuraEnabled public List<CaseComment> comments;

    public CaseWrapper(Case c, List<CaseComment> caseComments) {
        this.theCase = c;
        this.comments = caseComments;
    }
}

// In the controller:
List<Case> cases = [SELECT Id, Subject FROM Case WHERE ...];
Map<Id, List<CaseComment>> commentMap = buildCommentMap(cases);
List<CaseWrapper> rows = new List<CaseWrapper>();
for (Case c : cases) {
    rows.add(new CaseWrapper(c, commentMap.get(c.Id) ?? new List<CaseComment>()));
}
```

**Detection hint:** Any SOQL or DML statement inside a class constructor (`public ClassName(...)` block). This is almost always a governor-limit hazard in list-processing contexts.
