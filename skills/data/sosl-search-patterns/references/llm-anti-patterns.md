# LLM Anti-Patterns — SOSL Search Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce SOSL search patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using SOQL When SOSL Is the Right Tool

**What the LLM generates:** `SELECT Id, Name FROM Account WHERE Name LIKE '%acme%' OR BillingCity LIKE '%acme%' OR Description LIKE '%acme%'` — using SOQL with multiple LIKE clauses for full-text search instead of SOSL FIND.

**Why it happens:** SOQL is far more represented in training data than SOSL. LLMs default to SOQL for all data retrieval, including search scenarios where SOSL's full-text search index is dramatically more efficient.

**Correct pattern:**

```text
When to use SOSL instead of SOQL:

SOSL is better when:
- Searching across multiple fields simultaneously
- Searching across multiple objects in a single query
- User input is a search term (not a structured filter)
- Fields include Text, Long Text Area, Rich Text (full-text searchable)

SOQL is better when:
- Filtering on specific fields with known values
- Querying a single object with structured WHERE conditions
- Sorting, aggregation, or GROUP BY is needed
- Relationship queries (parent-child traversal)

SOSL example:
  FIND 'acme' IN ALL FIELDS RETURNING
    Account(Id, Name, BillingCity),
    Contact(Id, FirstName, LastName, Email)
```

**Detection hint:** Flag SOQL queries with 3+ LIKE clauses on text fields where a single SOSL FIND would be more efficient. Look for `LIKE '%term%'` patterns that indicate full-text search intent.

---

## Anti-Pattern 2: Not Escaping User Input in Dynamic SOSL (Search.query)

**What the LLM generates:** `List<List<SObject>> results = Search.query('FIND \'' + userInput + '\' IN ALL FIELDS RETURNING Account');` without escaping the user input, creating a SOSL injection vulnerability.

**Why it happens:** SOSL injection is less discussed than SQL injection in training data. LLMs generate dynamic SOSL with string concatenation the same way they generate dynamic SOQL, without applying Salesforce-specific escaping.

**Correct pattern:**

```text
SOSL injection prevention:

// WRONG - vulnerable to injection:
String query = 'FIND \'' + userInput + '\' RETURNING Account';
List<List<SObject>> results = Search.query(query);

// CORRECT - escape special characters:
String sanitized = String.escapeSingleQuotes(userInput);
// Also escape SOSL reserved characters:
sanitized = sanitized.replaceAll('[\\?\\&\\|\\!\\{\\}\\[\\]\\(\\)\\^\\~\\*:\\\\"\\\'+\\-]', '\\\\$0');
String query = 'FIND \'' + sanitized + '\' RETURNING Account';
List<List<SObject>> results = Search.query(query);

SOSL reserved characters that need escaping:
? & | ! { } [ ] ( ) ^ ~ * : \\ " ' + -

For simple cases, use static SOSL with bind variables:
  List<List<SObject>> results = [FIND :userInput IN ALL FIELDS RETURNING Account];
  // Bind variables in static SOSL are automatically escaped
```

**Detection hint:** Flag `Search.query()` calls that concatenate user input without `escapeSingleQuotes()` and SOSL character escaping. Regex: `Search\.query\(.*\+.*\)` without prior escaping.

---

## Anti-Pattern 3: Expecting SOSL Results to Return More Than 2,000 Records

**What the LLM generates:** "Use SOSL to search all 50,000 Contacts matching the search term" without noting that SOSL returns a maximum of 2,000 records per object by default (and 200 in Apex without LIMIT).

**Why it happens:** SOQL can return up to 50,000 records in Apex. LLMs apply the same assumption to SOSL without checking the different limits.

**Correct pattern:**

```text
SOSL return limits:

In Apex:
- Default: 200 records per object (if no LIMIT specified)
- Maximum: 2,000 records per object (with LIMIT 2000)
- Total across all objects: 2,000 records

In API (REST/SOAP):
- Maximum: 2,000 records total across all objects

Example with explicit limit:
  FIND 'acme' RETURNING Account(Id, Name LIMIT 500), Contact(Id, Name LIMIT 500)

If you need more than 2,000 matching records:
- SOSL is a search tool, not a bulk retrieval tool
- Use SOQL for structured bulk retrieval after SOSL narrows the scope
- Or use SOSL to get IDs, then SOQL: WHERE Id IN :soslResultIds
```

**Detection hint:** Flag SOSL usage where the expected result set exceeds 2,000 records. Check for missing LIMIT clauses in RETURNING clause (defaults to 200 in Apex).

---

## Anti-Pattern 4: Using Wildcards Incorrectly in FIND Clause

**What the LLM generates:** `FIND 'a*'` (single-character search term with wildcard) or `FIND '*'` (wildcard-only search), which either returns no results or throws an error because SOSL requires a minimum of 2 characters before a wildcard.

**Why it happens:** LLMs apply general regex or SQL wildcard patterns to SOSL without understanding the minimum character requirements and wildcard placement rules.

**Correct pattern:**

```text
SOSL wildcard rules:

* (asterisk): matches zero or more characters at middle or end of term
  - Valid: 'acm*' (matches acme, acmesoft, acmecorp)
  - Valid: 'ac*e' (matches acme, ace)
  - Invalid: '*acme' (leading wildcard — not supported in FIND clause)
  - Invalid: '*' (wildcard-only search)

? (question mark): matches exactly one character
  - Valid: 'ac?e' (matches acme, ache)
  - Invalid: '?' (single wildcard search)

Minimum search term length:
  - At least 2 characters before a wildcard
  - 'a*' is too short — Salesforce returns 0 results or an error

Phrase search: use double quotes
  - FIND '"John Smith"' (exact phrase match)
  - FIND '"John Smi*"' (phrase with trailing wildcard)
```

**Detection hint:** Flag SOSL FIND clauses with single-character terms followed by `*`, leading `*` wildcards, or wildcard-only patterns. Regex: `FIND\s+'[\?\*]'` or `FIND\s+'.\*'` with single character.

---

## Anti-Pattern 5: Not Specifying Search Scope (IN clause) for Performance

**What the LLM generates:** `FIND 'term' RETURNING Account` without specifying the search scope (IN ALL FIELDS, IN NAME FIELDS, IN EMAIL FIELDS, IN PHONE FIELDS, IN SIDEBAR FIELDS), defaulting to ALL FIELDS which searches every searchable field on every returned object.

**Why it happens:** The IN clause is optional and defaults to ALL FIELDS. Training data often omits it for brevity. However, searching ALL FIELDS is slower and may return false positives from Description or Comment fields.

**Correct pattern:**

```text
SOSL search scope (IN clause):

IN ALL FIELDS: searches all searchable fields (default, broadest, slowest)
IN NAME FIELDS: searches Name, Title, Subject, Email fields
IN EMAIL FIELDS: searches email-type fields only
IN PHONE FIELDS: searches phone-type fields only
IN SIDEBAR FIELDS: searches fields shown in sidebar search results

Performance optimization:
  // Broad search (slower, more results):
  FIND 'acme' IN ALL FIELDS RETURNING Account, Contact

  // Targeted search (faster, fewer false positives):
  FIND 'acme' IN NAME FIELDS RETURNING Account(Id, Name), Contact(Id, Name)

  // Email-specific search:
  FIND 'john@acme.com' IN EMAIL FIELDS RETURNING Contact(Id, Name, Email)

Always use the narrowest scope that satisfies the search requirement.
```

**Detection hint:** Flag SOSL queries on large result sets that use `IN ALL FIELDS` or omit the IN clause entirely. Recommend narrower scope (NAME FIELDS, EMAIL FIELDS) when the search intent is clear.
