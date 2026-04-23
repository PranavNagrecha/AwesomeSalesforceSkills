# Gotchas — Apex Regex And Pattern Matching

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `String.matches()` Is Implicitly Anchored

**What happens:** `'abc123'.matches('\\d+')` returns `false`, not `true`, and `'abc123'.matches('.*\\d+.*')` returns `true`.

**When it occurs:** Practitioners port a pattern from JavaScript's `.test()` or from regex101 (which defaults to unanchored) without realizing Apex `matches()` requires the full string.

**How to avoid:** For substring matching use `Matcher m = Pattern.compile(p).matcher(s); m.find();`. For whole-string validation keep using `matches()` and remember you don't need explicit `^...$`.

---

## Gotcha 2: `$` In Replacement Strings Is A Backreference

**What happens:** `'price'.replaceAll('price', '$9.99')` throws `IndexOutOfBoundsException: No group 9`. `'price'.replaceAll('price', '$1')` silently yields empty if there is no capture group.

**When it occurs:** Any replacement containing a literal dollar sign — currency, environment variables like `$USER`, or template markers.

**How to avoid:** Wrap replacement values with `Matcher.quoteReplacement(value)`. This escapes `$` and `\\` safely.

---

## Gotcha 3: 1,000,000 Character Hard Cap

**What happens:** Matching a pattern against a string larger than 1,000,000 characters throws `System.LimitException: regex too complicated` before the first match.

**When it occurs:** Scanning attachment text, large email bodies, concatenated notes, or rich text fields.

**How to avoid:** Guard `s.length()` before calling regex, chunk the string into windows, or scan line-by-line with `String.splitByRegExp` on a cheap delimiter first.

---

## Gotcha 4: Apex Regex Is Java, Not JavaScript

**What happens:** Patterns that work in Chrome DevTools fail to compile or produce wrong matches in Apex. Common pitfalls: variable-length lookbehind `(?<=\\w+)` (Java supported this only from 9+), `\\p{L}` unicode categories available but `\\p{Emoji}` not, no named group named by `(?P<name>...)` Python syntax.

**When it occurs:** Developers copy patterns from JavaScript MDN or Python documentation.

**How to avoid:** Test the pattern in a Java-based tester (regex101 "Java flavor") before shipping. Keep lookbehind fixed-length.

---

## Gotcha 5: Catastrophic Backtracking On User Input

**What happens:** A pattern like `(a+)+b` on input `aaaaaaaaaaaaaaaaaaaac` (no `b` anywhere) hangs the transaction until CPU timeout — the engine explores 2^n combinations.

**When it occurs:** Nested quantifiers (`+*`, `**`, `+?+`), alternation with overlap (`(a|a)+`), or greedy `.*` followed by a specific suffix.

**How to avoid:** Use bounded quantifiers (`{0,200}`), non-overlapping alternation, possessive quantifiers (`*+`, `++`), and explicit character classes (`[^@]+` instead of `.+@`).

---

## Gotcha 6: `String.split(regex)` Uses Regex, Not A Literal

**What happens:** `'a.b.c'.split('.')` returns `['', '', '', '', '', '']` because `.` matches every character, not a literal dot.

**When it occurs:** Splitting on `.`, `|`, `(`, `)`, `$`, `*`, or `+`.

**How to avoid:** Escape the delimiter: `str.split('\\.')`, or use `str.splitByCharacterType()` / manual `indexOf` if the delimiter is complex.

---

## Gotcha 7: `Pattern.compile` Is Not Cheap In A Loop

**What happens:** A trigger that calls `Pattern.compile('\\d+')` inside a `for` loop over 200 records spends measurable CPU on recompilation. This is invisible at small scale but shows up in bulk execution.

**When it occurs:** Any hot path that builds a pattern literal each iteration.

**How to avoid:** Move the pattern to a `private static final Pattern` field on the class; it compiles once per transaction.

---

## Gotcha 8: `replaceFirst` Is Case-Sensitive By Default

**What happens:** `'Hello World'.replaceFirst('hello', 'Hi')` returns the original string unchanged.

**When it occurs:** Practitioners expect string methods to be case-insensitive or to share flags with other Apex string APIs.

**How to avoid:** Use inline flags: `'Hello World'.replaceFirst('(?i)hello', 'Hi')`. The `(?i)` turns on case-insensitivity for the rest of the pattern.

---

## Gotcha 9: `Pattern.quote` Vs `Matcher.quoteReplacement` — Different Purposes

**What happens:** A developer escapes user input with `Matcher.quoteReplacement` and then passes it as a pattern; regex metacharacters are still active.

**When it occurs:** Confusion between escaping input for the *pattern* versus the *replacement*.

**How to avoid:** `Pattern.quote(s)` escapes `s` for use as a literal pattern. `Matcher.quoteReplacement(s)` escapes `s` for use as a literal replacement. Pick the one matching where the string goes.
