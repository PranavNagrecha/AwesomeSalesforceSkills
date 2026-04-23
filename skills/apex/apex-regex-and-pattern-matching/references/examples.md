# Examples — Apex Regex And Pattern Matching

## Example 1: Validating An E.164 Phone On Lead Insert

**Context:** Lead forms from multiple channels (web-to-lead, imports, partner APIs) all write into `Lead.Phone`. Sales wants only E.164-formatted phones reaching the dialer.

**Problem:** `String.matches()` is anchored — practitioners who write `phone.matches('\\+\\d+')` forget anchors are automatic, then add them and break. Others call `Pattern.compile(...)` inside the trigger handler, paying the compile cost on every record.

**Solution:**

```apex
public with sharing class LeadPhoneValidator {
    private static final Pattern E164 = Pattern.compile('^\\+[1-9]\\d{1,14}$');

    public static void validate(List<Lead> leads) {
        for (Lead l : leads) {
            if (String.isNotBlank(l.Phone) && !E164.matcher(l.Phone).matches()) {
                l.Phone.addError('Phone must be in E.164 format (e.g. +14155552671).');
            }
        }
    }
}
```

**Why it works:** The `Pattern` is compiled once per transaction in the static initializer. `matcher(...).matches()` is the whole-string form — no extra anchors, no accidental partial matches. Bounded `{1,14}` prevents ReDoS on oversize input.

---

## Example 2: Extracting Every Order Reference From An Email Body

**Context:** A Case trigger scans the incoming email body to link any `ORD-123456` references to the corresponding Order records for agent convenience.

**Problem:** A developer writes `emailBody.replaceAll('[^ORD-\\d+]', '')` and wonders why it returns garbage — character class negation doesn't work on multi-character tokens.

**Solution:**

```apex
public with sharing class EmailOrderLinker {
    private static final Pattern ORDER_REF = Pattern.compile('ORD-\\d{6,10}');

    public static List<String> findOrderRefs(String emailBody) {
        Set<String> unique = new Set<String>();
        if (String.isBlank(emailBody)) return new List<String>();
        Matcher m = ORDER_REF.matcher(emailBody);
        while (m.find()) {
            unique.add(m.group());
        }
        return new List<String>(unique);
    }
}
```

**Why it works:** `find()` returns each non-overlapping match. `group()` with no argument returns the whole matched substring. A `Set` deduplicates repeated references in long email threads.

---

## Example 3: Replacing Merge Tokens With User-Supplied Values

**Context:** An email template engine replaces `{{firstName}}`, `{{amount}}`, etc., with runtime values from a Map.

**Problem:** A user types `$5.00` in a custom field. The template engine uses `body.replaceAll('\\{\\{amount\\}\\}', value)` and throws `IndexOutOfBoundsException: No group 5`.

**Solution:**

```apex
public with sharing class TemplateRenderer {
    private static final Pattern TOKEN = Pattern.compile('\\{\\{(\\w+)\\}\\}');

    public static String render(String template, Map<String, String> values) {
        if (String.isBlank(template)) return template;
        Matcher m = TOKEN.matcher(template);
        StringBuilder sb = new StringBuilder();
        Integer cursor = 0;
        while (m.find()) {
            sb.append(template.substring(cursor, m.start()));
            String key = m.group(1);
            String v = values.containsKey(key) ? values.get(key) : '';
            sb.append(v == null ? '' : v);
            cursor = m.end();
        }
        sb.append(template.substring(cursor));
        return sb.toString();
    }
}
```

**Why it works:** Manual substring assembly bypasses the replacement-string parser entirely, so literal `$` and `\` in user values pass through unchanged. `StringBuilder` avoids quadratic concatenation on long templates.

---

## Anti-Pattern: Single Backslash In An Apex Regex Literal

**What practitioners do:**

```apex
Pattern p = Pattern.compile('\d{3}-\d{4}');
```

**What goes wrong:** Apex parses `\d` in a string literal the same way Java does — `\d` is not a valid escape, so the compile error is `Invalid escape character` or the pattern silently becomes `d{3}-d{4}` in Anonymous Apex. Practitioners paste patterns from JavaScript or regex101 verbatim and miss this every time.

**Correct approach:** Double every backslash in the source: `Pattern.compile('\\d{3}-\\d{4}')`.

---

## Anti-Pattern: Embedding User Input Into The Pattern, Not The Matcher

**What practitioners do:**

```apex
String hit = body.replaceAll(userKeyword, '');
```

**What goes wrong:** If `userKeyword` contains regex metacharacters (`.`, `+`, `(`, `[`), they are treated as regex, not as literal text. A user searching for `a.b` matches `aXb`, `a5b`, etc. Pasting `.*` wipes the entire string.

**Correct approach:** Escape user input with `Pattern.quote(...)`:

```apex
String safePattern = Pattern.quote(userKeyword);
String out = body.replaceAll(safePattern, '');
```
