# LLM Anti-Patterns — XSS and Injection Prevention

Common mistakes AI coding assistants make when generating or advising on XSS and injection prevention in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Raw Expression in Visualforce JavaScript Block

**What the LLM generates:** Visualforce code with `{!field}` directly inside a `<script>` block without JSENCODE.

**Why it happens:** LLMs are trained on many VF examples where `{!field}` works correctly — which is true in HTML body contexts. They generalize this pattern without knowing that the JavaScript rendering context is different.

**Correct pattern:**
```html
<!-- WRONG -->
<script>
    var name = '{!contact.LastName}';
</script>

<!-- CORRECT -->
<script>
    var name = '{!JSENCODE(contact.LastName)}';
</script>
```

**Detection hint:** Any `{!` expression inside a `<script>` block that is not wrapped in `JSENCODE(...)`.

---

## Anti-Pattern 2: String Concatenation in Dynamic SOQL

**What the LLM generates:** Dynamic SOQL with direct string concatenation using user-supplied values, often with `String.escapeSingleQuotes()` as a fix.

**Why it happens:** LLMs learn SQL-style query construction from many languages and apply the concatenation pattern. They may also learn the escapeSingleQuotes() pattern as "the Salesforce fix" without understanding its limitations.

**Correct pattern:**
```apex
// WRONG
String q = 'SELECT Id FROM Account WHERE Name = \''
    + String.escapeSingleQuotes(name) + '\'';

// CORRECT
String q = 'SELECT Id FROM Account WHERE Name = :name';
List<Account> results = Database.query(q);
```

**Detection hint:** Any `Database.query(` call where the string argument contains `+` concatenation with a variable. Bind variables use `:varName` syntax, not concatenation.

---

## Anti-Pattern 3: Trusting LWC Framework to Sanitize innerHTML

**What the LLM generates:** LWC JavaScript that sets `this.template.querySelector('div').innerHTML = apexData` and claims it is safe because LWC uses Lightning Web Security.

**Why it happens:** LLMs conflate LWS's cross-component isolation with XSS prevention. They are different things.

**Correct pattern:**
```javascript
// WRONG: innerHTML with Apex-returned data
this.template.querySelector('.container').innerHTML = this.richTextValue;

// CORRECT: use template binding which is auto-escaped
// In template: <div class="container">{richTextValue}</div>
// Or use lightning-formatted-rich-text for rich text (which sanitizes)
```

**Detection hint:** Any LWC JavaScript that sets `innerHTML` with a value that came from an Apex method or record field.

---

## Anti-Pattern 4: Using HTML Encoding in JavaScript Contexts

**What the LLM generates:** `{!HTMLENCODE(field)}` inside a JavaScript block, thinking it is safe.

**Why it happens:** LLMs know `HTMLENCODE` is a security function and reach for it as the generic "escape the output" answer, without asking which grammar the value is about to be parsed by.

**Why HTMLENCODE actually fails here** — the mechanism matters, because a wrong explanation gets repeated to developers as confidently as a right one:

A classic `<script>` element is a *raw text* element in the HTML parser. Its contents are **not** entity-decoded on the way to the JavaScript engine. So `HTMLENCODE` buys nothing: the `&#x27;` it emits is never turned back into `'`, but neither is it doing any work, and the characters that break a JavaScript string literal pass through untouched. `HTMLENCODE` does not escape the backslash, and it does not neutralise line terminators or the `</script>` sequence — all of which let an attacker terminate the quoted string and start writing code.

Note the frequently-repeated claim that "`&amp;` is valid HTML but also valid JS syntax that can form an XSS payload" is **not** the reason. `&` is the bitwise-AND operator in JavaScript and `&amp;` is not an XSS vector. The real reason is the raw-text parsing rule above.

`JSENCODE` inserts JavaScript escape characters (it escapes quotes, backslashes and control characters for a JS string-literal context), which is why it — and only it — is the correct control inside a script block.

**Correct pattern:**
```html
<!-- WRONG: HTMLENCODE in a JavaScript context -->
<script>
    var name = '{!HTMLENCODE(contact.Name)}';
</script>

<!-- CORRECT: JSENCODE in JavaScript contexts -->
<script>
    var name = '{!JSENCODE(contact.Name)}';
</script>
```

**Detection hint:** `HTMLENCODE` appearing anywhere between `<script>` and `</script>` — mechanically checkable with a parse of the Visualforce page. Two secondary tells worth flagging separately: (a) any *explanation* of this rule that invokes `&amp;` as a JavaScript payload, which is the fabricated rationale and signals the author reasoned from a memorised phrase rather than the parsing model; (b) `JSENCODE` used in an HTML attribute or element-body context, which is the mirror-image error — JSENCODE does not escape `<`, `>` or `&`, so it does not prevent HTML-context XSS.

---

## Anti-Pattern 5: Missing Whitelist on PageReference Redirect

**What the LLM generates:** An Apex controller that redirects to a URL parameter without validation, potentially using `PageReference.setRedirect(true)` to make it look intentional.

**Why it happens:** LLMs see PageReference redirect patterns in training data and add them without security validation. They may not be aware of open redirect as a vulnerability class.

**Correct pattern:**
```apex
// WRONG: unvalidated redirect
public PageReference doRedirect() {
    String url = ApexPages.currentPage().getParameters().get('next');
    return new PageReference(url);
}

// CORRECT: allowlist validation
private static final Set<String> SAFE_PATHS = new Set<String>{'/lightning/page/home'};
public PageReference doRedirect() {
    String url = ApexPages.currentPage().getParameters().get('next');
    if (url != null && SAFE_PATHS.contains(url)) {
        return new PageReference(url);
    }
    return Page.Home;
}
```

**Detection hint:** `new PageReference(` where the argument is a variable derived from `ApexPages.currentPage().getParameters()` or any user-supplied input without a preceding allowlist check.
