# LLM Anti-Patterns — Apex String and Regex

Mistakes AI coding assistants commonly make when generating Apex
String / regex code. The consuming agent should self-check against this
list before finalizing output.

---

## Anti-Pattern 1: `String.format` with printf-style placeholders

**What the LLM generates.**

```apex
String msg = String.format('Hello %s, you have %d cases',
    new List<Object>{ name, count });
// Output: 'Hello %s, you have %d cases'  ← placeholders not substituted
```

**Why it happens.** `String.format` is the same name as Java's
`String.format` (which IS printf-style) and Python's, C's, etc. The
LLM bleeds the printf syntax across runtimes.

**Correct pattern.**

```apex
String msg = String.format('Hello {0}, you have {1} cases',
    new List<String>{ name, String.valueOf(count) });
```

Apex uses Java MessageFormat: `{0}`, `{1}`. Arguments must be
`List<String>`.

**Detection hint.** Any `String.format(...)` call with `%s`, `%d`, `%f`,
`%n` is wrong in Apex.

---

## Anti-Pattern 2: Compiling a Pattern inside a loop

**What the LLM generates.**

```apex
for (Lead l : leads) {
    Pattern p = Pattern.compile('^[^@]+@[^@]+$');  // ← compiled per record
    if (p.matcher(l.Email).matches()) { ... }
}
```

**Why it happens.** Most general-purpose-language regex examples show
inline compilation because they're toy single-shot examples. The
LLM doesn't transfer the "hoist for hot path" optimization to Apex.

**Correct pattern.** `static final` at class scope:

```apex
private static final Pattern EMAIL_RE = Pattern.compile('^[^@]+@[^@]+$');

public static void handle(List<Lead> leads) {
    for (Lead l : leads) {
        if (EMAIL_RE.matcher(l.Email).matches()) { ... }
    }
}
```

**Detection hint.** Any `Pattern.compile(...)` call inside a `for`,
`while`, or batch `execute()` body is suspect.

---

## Anti-Pattern 3: `matches()` when extraction was wanted

**What the LLM generates.**

```apex
Pattern p = Pattern.compile('https?://\\S+');
if (p.matcher(body).matches()) {
    // tries to extract a URL from body — but matches() needs whole-input match
}
```

**Why it happens.** The verb "matches" reads naturally as "find a
match", which is `find()`'s job. `matches()`'s "whole input must
match" semantics is non-obvious from the name.

**Correct pattern.**

```apex
private static final Pattern URL_RE = Pattern.compile('https?://\\S+');

while (URL_RE.matcher(body).find()) {  // or: extract via Matcher state
    // ...
}
```

**Detection hint.** Whenever the regex doesn't end in `$` AND doesn't
match the whole expected input shape (e.g., `^foo$`), `matches()` is
likely wrong; `find()` is what the author meant.

---

## Anti-Pattern 4: `split` without `-1` when trailing empties matter

**What the LLM generates.**

```apex
List<String> fields = csvRow.split(',');  // ← drops trailing empties
```

**Why it happens.** The single-arg form is the most common across
languages; the `limit = -1` argument is documented but easy to miss.
Java tutorials often don't mention it.

**Correct pattern.**

```apex
List<String> fields = csvRow.split(',', -1);
```

**Detection hint.** Any `String.split(regex)` call (single-arg) where
the result is then indexed by position — `fields[3]`, `fields[4]` — is
a bug if the input might end with empty fields.

---

## Anti-Pattern 5: `Matcher.group()` without a `find()` / `matches()` gate

**What the LLM generates.**

```apex
Matcher m = pat.matcher(input);
String captured = m.group(1);  // ← throws if no match attempted
```

**Why it happens.** The LLM assumes the match succeeds and writes
straight-line code. The implicit precondition (`find()` / `matches()`
must have been called and returned true) isn't surfaced in the type
signature.

**Correct pattern.**

```apex
Matcher m = pat.matcher(input);
if (m.find()) {
    String captured = m.group(1);
}
```

**Detection hint.** Every `m.group(...)` call should have a guarding
`if (m.find())` or `if (m.matches())` in the same scope or earlier in
the control-flow path.

---

## Anti-Pattern 6: Calling instance methods on potentially-null Strings

**What the LLM generates.**

```apex
public static String normalize(String input) {
    return input.toLowerCase().trim();  // ← NPE if input is null
}
```

**Why it happens.** LLMs often assume non-null parameters. Apex's lack
of nullable-vs-non-null in the type signature doesn't force the
distinction.

**Correct pattern.**

```apex
public static String normalize(String input) {
    if (String.isBlank(input)) return '';
    return input.toLowerCase().trim();
}
```

Or use the safe-navigation operator (when null is acceptable):

```apex
return input?.toLowerCase()?.trim();
```

**Detection hint.** Any public method taking a `String` parameter that
calls instance methods on it without an early null/blank guard is at
risk. The fix is one line: `if (String.isBlank(input)) return ...;`.

---

## Anti-Pattern 7: `String.valueOf(null) == null` comparison

**What the LLM generates.**

```apex
String name = String.valueOf(account.Name);
if (name == null) { /* never true */ }
```

**Why it happens.** `String.valueOf` looks like a "convert to string,
preserving null" operation. It isn't — null becomes the string
`'null'`.

**Correct pattern.** Null-check the source before formatting:

```apex
String name = (account.Name == null) ? '(blank)' : account.Name;
// or
if (String.isBlank(account.Name)) { ... }
```

**Detection hint.** Any pattern of `String.valueOf(x)` followed by
`if (...) == null` or `if (... == '')` against the result is suspect.
Check the upstream null-source instead.
