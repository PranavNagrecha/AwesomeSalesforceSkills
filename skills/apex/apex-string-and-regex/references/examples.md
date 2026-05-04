# Examples — Apex String and Regex

## Example 1 — CSV row parser that doesn't drop trailing empties

**Context.** A bulk job parses CSV strings of the form `value,value,,,`
where trailing empties matter (e.g., a CSV with five required columns
where the last three are optional).

**Wrong instinct.**

```apex
List<String> fields = row.split(',');  // 'a,b,,,' → ['a', 'b']  ← only 2!
```

**Why it's wrong.** Apex's `String.split(regex)` delegates to Java's
`String.split` with `limit = 0`, which silently strips trailing empty
fields. The downstream code expects 5 fields and gets 2, often without
a clear error.

**Right answer.**

```apex
List<String> fields = row.split(',', -1);  // 'a,b,,,' → ['a', 'b', '', '', '']
```

`limit = -1` preserves all empties. Use it whenever the position of a
field matters more than its presence.

---

## Example 2 — Email validator with cached Pattern

**Context.** A trigger validates the `Email` field on every Lead in a
`before insert` / `before update` batch of up to 200 records. Compiling
the regex per record is the kind of "free" overhead that becomes 30 % of
the trigger's wall-clock at scale.

**Right answer.**

```apex
public class EmailValidator {
    private static final Pattern EMAIL_RE = Pattern.compile(
        '^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
    );

    public static Boolean isValid(String email) {
        if (String.isBlank(email)) return false;
        return EMAIL_RE.matcher(email).matches();
    }
}
```

`static final` ensures one compile per class load. `String.isBlank` is
the null-safe entry guard.

---

## Example 3 — Extract every URL from a body

**Context.** Email body parsed for outbound URLs (audit trail, link
hygiene, security review).

**Wrong instinct.**

```apex
Pattern p = Pattern.compile('https?://\\S+');
String url = p.matcher(body).matches() ? body : null;  // ← matches() = whole-string
```

**Why it's wrong.** `matches()` requires the whole body to be a URL.
The author wanted "find any URL" — that's `find()`.

**Right answer.**

```apex
private static final Pattern URL_RE = Pattern.compile('https?://\\S+');

public static List<String> extractUrls(String body) {
    List<String> out = new List<String>();
    if (String.isBlank(body)) return out;
    Matcher m = URL_RE.matcher(body);
    while (m.find()) {
        out.add(m.group());
    }
    return out;
}
```

The `while (m.find())` loop is the standard Apex idiom for
"every-occurrence" extraction.

---

## Example 4 — `String.format` template with the right placeholder syntax

**Context.** Build a notification message with two substitutions.

**Wrong instinct.**

```apex
String msg = String.format('Hello %s, you have %d new cases.',
    new List<Object>{ user.FirstName, caseCount });
// Output: 'Hello %s, you have %d new cases.'  ← placeholders not substituted
```

**Why it's wrong.** Apex's `String.format` uses Java `MessageFormat`
syntax (`{0}`, `{1}`), not C/printf-style. The `%s` and `%d` survive
literally.

**Right answer.**

```apex
String msg = String.format('Hello {0}, you have {1} new cases.',
    new List<String>{ user.FirstName, String.valueOf(caseCount) });
```

Note: arguments must be a `List<String>`, and numbers / IDs need
`String.valueOf()` first.

---

## Example 5 — Capture group with ID extraction

**Context.** Parse a Salesforce 18-character record ID out of a body of
free text and look up the record.

**Right answer.**

```apex
private static final Pattern ID_RE = Pattern.compile('([a-zA-Z0-9]{18})');

public static Id firstId(String body) {
    if (String.isBlank(body)) return null;
    Matcher m = ID_RE.matcher(body);
    if (!m.find()) return null;       // ← gate group() on a successful find()
    try {
        return Id.valueOf(m.group(1));
    } catch (System.StringException e) {
        return null;                   // wasn't a real ID despite the shape
    }
}
```

`m.group(1)` is the first capture group. **Calling group(1) without a
preceding successful `find()` or `matches()` throws `System.StringException`** —
always gate it.

---

## Anti-Pattern: `String.valueOf(null) == null`

```apex
String name = String.valueOf(account.Name);  // account.Name is null
if (name == null) {                           // ← never true
    // dead code
}
```

**What goes wrong.** `String.valueOf(null)` returns the four-character
string `'null'`. The comparison to literal `null` is always false.

**Correct.** Use `String.isBlank(account.Name)` before formatting, or
just compare to the literal string `'null'` if you really mean
"the string null":

```apex
if (account.Name == null || account.Name == '') { ... }
// or
if (String.isBlank(account.Name)) { ... }
```
