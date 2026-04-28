# LLM Anti-Patterns — Apex Dynamic SOQL Binding Safety

Common mistakes AI coding assistants make when generating or advising on dynamic SOQL in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Relying on `String.escapeSingleQuotes` as the only defense

**What the LLM generates:**

```apex
String safe = String.escapeSingleQuotes(userInput);
List<Account> accs = Database.query('SELECT Id FROM Account WHERE Name = \'' + safe + '\'');
```

**Why it happens:** `escapeSingleQuotes` is the most-cited Apex security primitive in training data, so the model treats it as a complete fix. It only addresses single-quote breakout in string-literal contexts.

**Correct pattern:**

```apex
Map<String, Object> binds = new Map<String, Object>{ 'name' => userInput };
List<Account> accs = Database.queryWithBinds(
    'SELECT Id FROM Account WHERE Name = :name',
    binds,
    AccessLevel.USER_MODE
);
```

**Detection hint:** Regex `Database\.query\s*\(.*escapeSingleQuotes` or `escapeSingleQuotes.*Database\.query` flags this co-occurrence.

---

## Anti-Pattern 2: Concatenating field names from user input without allowlisting

**What the LLM generates:**

```apex
String soql = 'SELECT Id, ' + userField + ' FROM Account LIMIT 10';
List<SObject> rows = Database.query(soql);
```

**Why it happens:** The model recognizes that bind variables protect values, then over-generalizes to "binding handles user input" without realizing identifiers cannot be bound at all.

**Correct pattern:**

```apex
Schema.SObjectField sf = Schema.SObjectType.Account.fields.getMap().get(userField.toLowerCase());
if (sf == null) throw new IllegalArgumentException('Unknown field');
String safeField = sf.getDescribe().getName();
String soql = 'SELECT Id, ' + safeField + ' FROM Account LIMIT 10';
```

**Detection hint:** Any `Database.query` (or its string assignment) that concatenates a variable BETWEEN `SELECT` and `FROM` without a Schema describe call upstream.

---

## Anti-Pattern 3: Passing `String` for LIMIT or OFFSET

**What the LLM generates:**

```apex
String soql = 'SELECT Id FROM Account LIMIT ' + userLimitString;
```

**Why it happens:** The model treats LIMIT as another part of the string template; it does not occur to it that a String can carry `100; DELETE FROM Account` or `100 OFFSET 9999`.

**Correct pattern:**

```apex
Integer cap = Math.min(Integer.valueOf(userLimitString), 200);
Map<String, Object> binds = new Map<String, Object>{ 'cap' => cap };
String soql = 'SELECT Id FROM Account LIMIT :cap';
List<Account> accs = Database.queryWithBinds(soql, binds, AccessLevel.USER_MODE);
```

**Detection hint:** Regex `LIMIT\s*'?\s*\+\s*\w+` where the variable type is not `Integer`.

---

## Anti-Pattern 4: `Database.query` with `:variable` not in scope

**What the LLM generates:**

```apex
public List<Account> search(String term) {
    String soql = buildSoql();   // returns 'SELECT Id FROM Account WHERE Name = :term'
    return Database.query(soql); // term is in scope here, accidentally works
}
public List<Account> wrapper() {
    String soql = 'SELECT Id FROM Account WHERE Name = :term';
    return Database.query(soql); // QueryException: Variable does not exist: term
}
```

**Why it happens:** The model treats `:varName` as a templating syntax and forgets the variable must exist as a local at the executing line.

**Correct pattern:**

```apex
return Database.queryWithBinds(
    'SELECT Id FROM Account WHERE Name = :term',
    new Map<String, Object>{ 'term' => term },
    AccessLevel.USER_MODE
);
```

**Detection hint:** `Database.query(...)` calls where the surrounding method has no local variable matching every `:name` token in the string.

---

## Anti-Pattern 5: Allowlist `if (allowed.contains(field))` without case normalization

**What the LLM generates:**

```apex
Set<String> allowed = new Set<String>{ 'Name', 'Industry', 'AnnualRevenue' };
if (!allowed.contains(userField)) throw new IllegalArgumentException();
String soql = 'SELECT Id, ' + userField + ' FROM Account';
```

**Why it happens:** The model picks an allowlist pattern (good) but stops there, missing that Apex `Set<String>.contains` is case-sensitive and that field API names are case-insensitive in SOQL.

**Correct pattern:**

```apex
Set<String> allowed = new Set<String>{ 'name', 'industry', 'annualrevenue' };
String key = (userField == null) ? '' : userField.toLowerCase();
if (!allowed.contains(key)) throw new IllegalArgumentException();
// then look up canonical name via Schema describe before concatenating
String safeField =
    Schema.SObjectType.Account.fields.getMap().get(key).getDescribe().getName();
String soql = 'SELECT Id, ' + safeField + ' FROM Account';
```

**Detection hint:** A `Set<String>` allowlist of field names where neither side of `.contains` is lowercased.

---

## Anti-Pattern 6: Treating `WITH USER_MODE` as a substitute for binding

**What the LLM generates:**

```apex
String soql = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\' WITH USER_MODE';
List<Account> accs = Database.query(soql);
```

**Why it happens:** The model conflates "FLS enforcement" with "injection prevention" because both sit under the security umbrella.

**Correct pattern:** Bind the value AND use `AccessLevel.USER_MODE`:

```apex
Map<String, Object> binds = new Map<String, Object>{ 'name' => userInput };
List<Account> accs = Database.queryWithBinds(
    'SELECT Id FROM Account WHERE Name = :name',
    binds,
    AccessLevel.USER_MODE
);
```

**Detection hint:** `WITH USER_MODE` or `WITH SECURITY_ENFORCED` co-occurring with string concatenation of variables in the same query.
