# Gotchas — Apex String and Regex

Non-obvious behaviors of Apex's String / Pattern / Matcher classes that
cause real production bugs.

---

## Gotcha 1: `String.split(regex)` silently drops trailing empty fields

**What happens.** `'a,b,,,'.split(',')` returns `['a', 'b']` — only two
elements, not five. The trailing empty fields are discarded.

**When it occurs.** CSV / pipe-delimited / tab-separated parsing where
the position of an empty field matters.

**Why.** Apex delegates to Java's `String.split` with `limit = 0`,
which strips trailing empty matches. Documented but constantly
forgotten.

**How to avoid.** Use the two-arg form with `limit = -1` to preserve
trailing empties:

```apex
List<String> parts = row.split(',', -1);  // ['a', 'b', '', '', '']
```

---

## Gotcha 2: `String.format` uses MessageFormat, not printf

**What happens.** `String.format('Hello %s', new List<String>{ 'world' })`
returns `'Hello %s'` — the `%s` is not substituted.

**When it occurs.** Anywhere a developer with C / Python / Java printf
muscle memory writes a format string.

**Why.** Apex's `String.format` is a thin wrapper around Java
`MessageFormat`. Placeholders are `{0}`, `{1}`, `{2}` (zero-indexed).

**How to avoid.**

```apex
String msg = String.format('Hello {0}, you have {1} cases',
    new List<String>{ name, String.valueOf(count) });
```

Numbers must be converted to strings via `String.valueOf` first; the
arguments list is `List<String>`, not `List<Object>`.

---

## Gotcha 3: Per-record `Pattern.compile` is silently expensive

**What happens.** A trigger that compiles a regex inside its loop
spends most of its CPU on regex parsing, not matching. At 200 records
per batch, this can be 30 % of the trigger's wall-clock — invisible
until you profile.

**When it occurs.** Trigger handlers, batch `execute()` methods, queueable
`execute()` methods. Anywhere a Pattern is constructed inside a loop.

**How to avoid.** Hoist the Pattern to class scope:

```apex
public class MyHandler {
    private static final Pattern EMAIL_RE = Pattern.compile('^[^@]+@[^@]+$');

    public static void handle(List<Lead> leads) {
        for (Lead l : leads) {
            if (EMAIL_RE.matcher(l.Email).matches()) { ... }
        }
    }
}
```

Once-per-class-load instead of once-per-record.

---

## Gotcha 4: `Matcher.group()` without prior `find()` / `matches()` throws

**What happens.** Calling `m.group()` or `m.group(1)` before a successful
`find()` (or `matches()`) call throws `System.StringException: No match
attempted`.

**When it occurs.** Hot fix code that assumed the match would succeed,
or a refactor that moved the `find()` call without bringing `group()`
along.

**How to avoid.** Always gate `group()`:

```apex
Matcher m = pat.matcher(input);
if (m.find()) {
    String captured = m.group(1);
} else {
    // no match — handle the absence
}
```

For `matches()`, the same rule holds — call `m.matches()` first, then
`m.group(...)` only inside the true branch.

---

## Gotcha 5: `String.valueOf(null)` returns the string `'null'`, not actual null

**What happens.** `String.valueOf(account.Name)` where `account.Name` is
null returns the 4-character string `'null'`. Comparing the result to
`null` is always false.

**When it occurs.** Building log messages, building debug strings, or
any "stringify this thing" call where the input might be null.

**How to avoid.** Null-check the source before formatting, or use the
elvis-style guard:

```apex
String safe = (account.Name != null) ? account.Name : '(no name)';
// or
String name = String.isNotBlank(account.Name) ? account.Name : '(no name)';
```

---

## Gotcha 6: `Matcher.matches()` requires the *entire* string to match

**What happens.** A regex like `'foo'` against `'hello foo world'` —
`m.matches()` returns false; `m.find()` returns true. Authors write
`matches()` expecting it to mean "find a match anywhere".

**When it occurs.** "Validate or extract?" decisions where the author
defaults to `matches()` because it sounds right.

**How to avoid.** The mental model:
- Validation (entire input must match a shape): `matches()`.
- Extraction (find one or more substrings): `find()`, often in a `while` loop.

If your regex doesn't end in `$` and your call is `matches()`, you
probably wanted `find()`.

---

## Gotcha 7: `$` in `replaceAll` replacement is a backreference, not a literal

**What happens.** `s.replaceAll('foo', '$1.99')` either throws or
silently breaks, because `$1` is interpreted as a backreference to a
capture group that doesn't exist.

**When it occurs.** Replacing with strings that contain currency symbols
or `$` followed by a digit.

**How to avoid.** Two options:

```apex
// Option 1: escape the $
String out = s.replaceAll('foo', '\\$1.99');

// Option 2: quoteReplacement (preferred — handles all special chars)
String safe = Matcher.quoteReplacement('$1.99');
String out = s.replaceAll('foo', safe);
```

`Matcher.quoteReplacement` is the bulletproof choice when the
replacement string is data, not a literal.
