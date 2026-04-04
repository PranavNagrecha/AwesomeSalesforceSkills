# LLM Anti-Patterns — Dynamic Apex

Common mistakes AI coding assistants make when generating or advising on Dynamic Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: String Concatenation of User Input Without Bind Variables

**What the LLM generates:**

```apex
String userSearch = ApexPages.currentPage().getParameters().get('q');
String query = 'SELECT Id, Name FROM Account WHERE Name = \'' + userSearch + '\'';
List<Account> results = Database.query(query);
```

**Why it happens:** LLMs trained on general programming corpora absorb the SQL string-building pattern from languages that do not support bind syntax in dynamic queries. In Apex the idiom looks superficially similar to Python or Java JDBC code, and the model replicates it without recognizing that Apex bind variables are a first-class feature.

**Correct pattern:**

```apex
String userSearch = ApexPages.currentPage().getParameters().get('q');
// Bind variable — not concatenated, not injectable
String query = 'SELECT Id, Name FROM Account WHERE Name = :userSearch';
List<Account> results = Database.query(query);
```

**Detection hint:** Look for `'\'' +` or `'"` + in a `Database.query()` argument string. Any quote-wrapped concatenation of a runtime variable in a query string is a red flag.

---

## Anti-Pattern 2: Skipping FLS Checks in Dynamic Field Access

**What the LLM generates:**

```apex
// Iterate over configurable field list and read values
for (String fieldName : configuredFields) {
    Object val = record.get(fieldName);
    results.put(fieldName, val);
}
```

**Why it happens:** FLS enforcement is invisible in static SOQL with `WITH USER_MODE` but must be explicit for dynamic access. LLMs commonly omit the FLS check because it is absent in most training examples, which focus on "does the code work" rather than "does the code enforce security."

**Correct pattern:**

```apex
Map<String, Schema.SObjectField> fieldMap =
    Schema.getGlobalDescribe().get(objectApiName).getDescribe().fields.getMap();

for (String fieldName : configuredFields) {
    String normalizedName = fieldName.toLowerCase();
    if (!fieldMap.containsKey(normalizedName)) {
        continue; // Field does not exist on schema
    }
    Schema.DescribeFieldResult fdr = fieldMap.get(normalizedName).getDescribe();
    if (!fdr.isAccessible()) {
        continue; // Current user lacks read access
    }
    Object val = record.get(fdr.getName());
    results.put(fdr.getName(), val);
}
```

**Detection hint:** Any `record.get(fieldName)` or `record.put(fieldName, ...)` inside a loop or configurable iteration path that has no preceding `isAccessible()` / `isUpdateable()` check.

---

## Anti-Pattern 3: Calling Schema.getGlobalDescribe() Inside a Loop

**What the LLM generates:**

```apex
for (SObject rec : records) {
    Map<String, Schema.SObjectField> fieldMap =
        Schema.getGlobalDescribe().get(rec.getSObjectType().getDescribe().getName())
              .getDescribe().fields.getMap();
    // process fields...
}
```

**Why it happens:** LLMs generate self-contained, "correct" code for the loop body in isolation. The describe call looks like a reasonable way to get the field map for each record's type. The model does not reason about the cumulative governor limit cost across records.

**Correct pattern:**

```apex
// Cache outside the loop — populated once, reused per iteration
private static final Map<String, Schema.SObjectType> GLOBAL_DESCRIBE =
    Schema.getGlobalDescribe();
private static final Map<String, Map<String, Schema.SObjectField>> FIELD_MAP_CACHE =
    new Map<String, Map<String, Schema.SObjectField>>();

for (SObject rec : records) {
    String objectName = rec.getSObjectType().getDescribe().getName().toLowerCase();
    if (!FIELD_MAP_CACHE.containsKey(objectName)) {
        FIELD_MAP_CACHE.put(objectName,
            GLOBAL_DESCRIBE.get(objectName).getDescribe().fields.getMap());
    }
    Map<String, Schema.SObjectField> fieldMap = FIELD_MAP_CACHE.get(objectName);
    // process fields...
}
```

**Detection hint:** `Schema.getGlobalDescribe()` or `.getDescribe()` call appearing inside a `for`, `while`, or iterator body without a prior cache check.

---

## Anti-Pattern 4: Using String.escapeSingleQuotes() on Field and Object Names

**What the LLM generates:**

```apex
String objectName = String.escapeSingleQuotes(userProvidedObject);
String fieldName  = String.escapeSingleQuotes(userProvidedField);
String query = 'SELECT ' + fieldName + ' FROM ' + objectName;
List<SObject> results = Database.query(query);
```

**Why it happens:** `String.escapeSingleQuotes()` is the most widely documented Apex injection defense and LLMs apply it reflexively to any dynamic string. The model does not distinguish between string literal values (which go inside quotes in SOQL) and identifiers (field/object names, which are unquoted and not protected by quote-escaping).

**Correct pattern:**

```apex
// Allowlist against live Schema metadata
Map<String, Schema.SObjectType> globalDescribe = Schema.getGlobalDescribe();
if (!globalDescribe.containsKey(userProvidedObject.toLowerCase())) {
    throw new IllegalArgumentException('Invalid object: ' + userProvidedObject);
}
Schema.DescribeSObjectResult objDescribe =
    globalDescribe.get(userProvidedObject.toLowerCase()).getDescribe();

Map<String, Schema.SObjectField> fieldMap = objDescribe.fields.getMap();
if (!fieldMap.containsKey(userProvidedField.toLowerCase())) {
    throw new IllegalArgumentException('Invalid field: ' + userProvidedField);
}
String validatedField  = fieldMap.get(userProvidedField.toLowerCase()).getDescribe().getName();
String validatedObject = objDescribe.getName();
String query = 'SELECT ' + validatedField + ' FROM ' + validatedObject;
```

**Detection hint:** `escapeSingleQuotes()` applied to a value that is then placed before `FROM` or in the `SELECT` list rather than inside a `=`, `LIKE`, or `IN` clause.

---

## Anti-Pattern 5: Assuming WITH SECURITY_ENFORCED Silently Filters Inaccessible Fields

**What the LLM generates:**

```apex
// "Safe" dynamic query — inaccessible fields are just ignored
String query = 'SELECT ' + String.join(fieldNames, ', ')
    + ' FROM Account WITH SECURITY_ENFORCED';
List<Account> results = Database.query(query);
```

**Why it happens:** The name "SECURITY_ENFORCED" implies the platform will handle security without developer effort, and that inaccessible fields will be gracefully excluded. LLMs propagate this misunderstanding from misleading colloquial usage they have encountered in training data.

**Correct pattern:**

```apex
// Pre-filter to only accessible fields; do not rely on WITH SECURITY_ENFORCED
// to produce graceful degradation.
Map<String, Schema.SObjectField> fieldMap =
    Schema.getGlobalDescribe().get('Account').getDescribe().fields.getMap();

List<String> accessibleFields = new List<String>{'Id'};
for (String fieldName : fieldNames) {
    String normalized = fieldName.toLowerCase();
    if (fieldMap.containsKey(normalized)
            && fieldMap.get(normalized).getDescribe().isAccessible()) {
        accessibleFields.add(fieldMap.get(normalized).getDescribe().getName());
    }
}
String query = 'SELECT ' + String.join(accessibleFields, ', ') + ' FROM Account';
List<Account> results = Database.query(query);
```

**Detection hint:** `WITH SECURITY_ENFORCED` in a dynamic SOQL string where the intent is partial results (graceful degradation) rather than strict enforcement. If the business requirement is "show what the user can see," pre-filter is correct. If it is "fail if any field is missing," `WITH SECURITY_ENFORCED` is appropriate — but document the intent.

---

## Anti-Pattern 6: Omitting Schema Validation When Using Dynamic SOSL

**What the LLM generates:**

```apex
String searchTerm = userInput;
String soslQuery = 'FIND \'' + searchTerm + '\' IN ALL FIELDS RETURNING Account(Name), Contact(Name)';
List<List<SObject>> results = Search.query(soslQuery);
```

**Why it happens:** LLMs treat dynamic SOSL as less risky than dynamic SOQL because the pattern is less discussed in security guidance. The same injection risks apply: unescaped single quotes or special SOSL metacharacters (`?`, `*`, `{`, `}`) in the search term alter query behavior.

**Correct pattern:**

```apex
// Use String.escapeSingleQuotes() for FIND clause values.
// SOSL does not support bind variables in the FIND clause.
String safeTerm = String.escapeSingleQuotes(userInput);
String soslQuery = 'FIND \'' + safeTerm + '\' IN ALL FIELDS RETURNING Account(Name), Contact(Name)';
List<List<SObject>> results = Search.query(soslQuery);
```

Note: SOSL's `FIND` clause does not support Apex bind variables as of Spring '25. `String.escapeSingleQuotes()` is the correct and only defense here — unlike SOQL WHERE clause values where bind variables are preferred.

**Detection hint:** Any `Search.query()` call where the `FIND` term is a runtime string without `escapeSingleQuotes()` applied.
