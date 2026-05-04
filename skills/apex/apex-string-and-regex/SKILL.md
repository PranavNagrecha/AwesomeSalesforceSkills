---
name: apex-string-and-regex
description: "Apex String class methods, Pattern/Matcher regex, text parsing, template rendering, and the null-safety landmines that bite every Apex programmer eventually. Covers `String.split` trailing-empty-drop semantics, `Pattern.compile` static-final caching, `Matcher.group` ordering rules, and the `String.format` MessageFormat-vs-printf trap. NOT for formula functions (FORMULA / TEXT in formula fields), NOT for SOQL string-bind escaping (see apex/dynamic-soql)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "apex split string drops trailing empty values"
  - "pattern matcher regex compile per record performance"
  - "string.format placeholder not substituted"
  - "matcher group throws stringexception when no match"
  - "null pointer exception on string method apex"
  - "apex regex global match all occurrences"
tags:
  - string
  - regex
  - pattern
  - matcher
  - text-parsing
  - null-safety
inputs:
  - "Apex code that parses, formats, or validates text"
  - "Whether the input can be null (it usually can; be explicit)"
  - "Whether the regex runs once per request or per record (loop hot path)"
outputs:
  - "Idiomatic String / Pattern usage with the correct null-safety guard"
  - "Pre-compiled Pattern stored as `static final` when used in a loop"
  - "Substitution via `String.format` with `{0}` / `{1}` placeholders, not `%s`"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Apex String and Regex

The Apex String class plus `Pattern` / `Matcher` is the everyday text-handling
toolkit in Salesforce. Most Apex programmers learn it through error messages —
`NullPointerException` on a method call, `System.StringException` from an
`m.group()` with no preceding `find()`, a `String.split` result that's missing
the last element, a `String.format` that prints `%s` literally. This skill
encodes the boundary rules and the right-shape-first patterns so those errors
stop happening.

What this skill is NOT. Formula-language `TEXT()` / `FORMULA()` is a different
runtime — go to the formula reference. SOQL string-binding (preventing
injection in dynamic queries) lives in `apex/dynamic-soql` because the
escaping rules are SOQL-specific, not String-class-specific.

---

## Before Starting

- Identify whether the input string can be **null**. Assume yes unless you
  can name the upstream check that already enforced non-null.
- Identify whether the call is on the **hot path** (loop body, trigger,
  per-record callout). If yes, any `Pattern.compile(...)` belongs at class
  scope as `static final`, not inline.
- Identify whether you want the **first match** or **every match**. Apex's
  default `Matcher.matches()` is *full-string match*, not "find a match
  anywhere" — that's `find()`. Choosing wrong is the most common regex bug.

---

## Core Concepts

### Null-safety: which methods crash, which return null, which return false

Apex's String class has three different null-handling shapes; mixing them is
the source of half the production bugs.

| Method | Null input behavior |
|---|---|
| `s.length()`, `s.toLowerCase()`, `s.contains(...)`, etc. (instance methods) | **NullPointerException** — `s` is null |
| `String.isBlank(s)`, `String.isNotBlank(s)`, `String.isEmpty(s)` | **Null-safe** — returns boolean |
| `String.valueOf(o)` where `o` is null | **Returns 'null'** (the four-character string), not actual null |
| `s.split(regex)` where `s` is null | **NullPointerException** |
| `String.escapeSingleQuotes(s)` where `s` is null | **Returns null** (does not crash) |

The right pattern: gate every instance-method call on a `String.isNotBlank`
check, or use the safe-navigation operator `?.` if you only need the call's
result and `null` is acceptable.

### Pattern compilation cost

`Pattern.compile(regex)` parses and builds a state machine. In a loop body
(trigger, batch handler) this dominates wall-clock if it runs per record.
The fix is at most three lines:

```apex
public class EmailValidator {
    private static final Pattern EMAIL_RE =
        Pattern.compile('^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$');

    public static Boolean isValid(String s) {
        if (String.isBlank(s)) return false;
        return EMAIL_RE.matcher(s).matches();
    }
}
```

`static final` means compiled once at class load, reused for every record.

### `matches()` vs `find()` — the regex bug everyone makes once

`Matcher.matches()` requires the **entire string** to match the regex.
`Matcher.find()` searches for **any substring** that matches.

```apex
Pattern p = Pattern.compile('foo');
Matcher m1 = p.matcher('hello foo world');
m1.matches(); // false — entire string is not "foo"
m1.find();    // true  — substring "foo" found

Matcher m2 = p.matcher('foo');
m2.matches(); // true  — entire string is "foo"
m2.find();    // true
```

Use `matches()` for validation (whole input must match). Use `find()` (often
in a `while (m.find())` loop) for extraction.

### `Matcher.group()` requires a successful match first

```apex
Matcher m = Pattern.compile('(\\d+)').matcher('abc');
String g = m.group(1);  // throws System.StringException
```

The fix is always to gate `group()` on a successful `find()` (or `matches()`):

```apex
Matcher m = Pattern.compile('(\\d+)').matcher(input);
if (m.find()) {
    String captured = m.group(1);
}
```

---

## Common Patterns

### Pattern A — Validate the entire input

```apex
private static final Pattern PHONE_RE = Pattern.compile('^\\+?[0-9 ()-]{7,20}$');

public static Boolean isValidPhone(String s) {
    if (String.isBlank(s)) return false;
    return PHONE_RE.matcher(s).matches();
}
```

`matches()`, not `find()`. Whole-input validation.

### Pattern B — Extract every occurrence

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

`find()` in a loop. `m.group()` (no argument) returns the whole match;
`m.group(1)`, `m.group(2)` return the numbered capture groups.

### Pattern C — Template substitution with `String.format`

```apex
String greeting = String.format('Hello {0}, you have {1} new cases.',
    new List<String>{ user.FirstName, String.valueOf(caseCount) });
```

**The trap.** Apex's `String.format` uses Java `MessageFormat` syntax
(`{0}`, `{1}`), **not** printf-style (`%s`, `%d`). If you pass `'Hello %s'`
the `%s` survives literally into the output.

The arguments must be a `List<String>`. Numbers get `String.valueOf()` first.

### Pattern D — Safe replace-all with backreferences

```apex
// Quote every word that starts with capital letter.
Pattern p = Pattern.compile('\\b([A-Z][a-z]+)\\b');
String quoted = p.matcher(input).replaceAll('"$1"');
```

`replaceAll('$1')` references the first capture group. Beware: `$` is a
special character — to use a literal `$` in the replacement, escape with
`\\$` or use `Matcher.quoteReplacement(literal)`.

### Pattern E — Split that doesn't drop trailing empty fields

```apex
// CSV row "a,b,,," — what we expect: 4 fields including 2 empty trailing
List<String> parts1 = 'a,b,,,'.split(',');        // returns ['a', 'b'] — empties dropped
List<String> parts2 = 'a,b,,,'.split(',', -1);    // returns ['a', 'b', '', '', '']
```

The two-arg form `split(regex, limit)` with `limit = -1` preserves trailing
empties. With `limit = 0` (the default) Java drops trailing empty strings.
This rule is documented but constantly forgotten.

---

## Decision Guidance

| Task | Use this | Reason |
|---|---|---|
| "Is this entire string a valid email?" | `Pattern.matcher(s).matches()` | matches = whole input; find = substring |
| "Pull every URL out of this body" | `while (m.find())` + `m.group()` | find = repeatable; group() returns the match |
| "Replace every digit with `*`" | `s.replaceAll('\\d', '*')` (String method, no Pattern needed) | Convenience method when the regex is one-shot |
| "Loop over 200 records, validating each" | `static final Pattern` + `matcher(s).matches()` | Avoid per-record `Pattern.compile` cost |
| "Build `'Hello {name}'` template" | `String.format('Hello {0}', new List<String>{ name })` | MessageFormat syntax, not printf |
| "Split and keep trailing empties" | `s.split(regex, -1)` | Java limit-0 drops trailing empties silently |
| "Null-check before any `.method()` call" | `String.isNotBlank(s)` | Null-safe; avoids NPE |

---

## Recommended Workflow

1. **Decide validation vs extraction.** Validation = whole-string match (`matches()`); extraction = `find()` in a loop. Wrong choice is the most common regex bug.
2. **Decide compile site.** Class-level `static final Pattern` if used more than once per request; inline `Pattern.compile` only for genuinely one-shot use.
3. **Add the null guard.** Every public entry point that takes a String parameter starts with `if (String.isBlank(s)) return ...;` (or the equivalent for your contract — false, null, empty list).
4. **Pick the right replace.** `s.replaceAll(regex, replacement)` for one-off replace; `Matcher.replaceAll` when you need backreferences and a pre-compiled Pattern.
5. **For templates: `String.format` with `{0}`, `{1}`.** Not `%s` — that's printf, which Apex doesn't use.
6. **Test the null and empty cases explicitly.** Don't rely on "the caller wouldn't pass null". Inspect the caller; if the caller could, your method must handle it.

---

## Review Checklist

- [ ] Every Pattern used in a loop is declared `static final` at class scope.
- [ ] Every `Matcher.group(...)` call is preceded by a successful `find()` or `matches()` in the same control-flow path.
- [ ] No `String.format(...)` uses `%s` / `%d`; all placeholders are `{0}`, `{1}`.
- [ ] Every public method accepting a String parameter null-guards its inputs.
- [ ] `s.split(regex, -1)` is used when trailing-empty fields matter.
- [ ] Replacement strings containing `$` are escaped (`Matcher.quoteReplacement(...)` or `\\$`).
- [ ] `matches()` vs `find()` choice matches the intent (validation vs extraction).

---

## Salesforce-Specific Gotchas

1. **`String.split(regex)` drops trailing empty strings.** Use `split(regex, -1)` to preserve them. (See `references/gotchas.md` § 1.)
2. **`String.format` uses MessageFormat (`{0}`), not printf (`%s`).** `%s` survives literally into the output. (See `references/gotchas.md` § 2.)
3. **Per-record `Pattern.compile()` is silently expensive.** Move to `static final`. (See `references/gotchas.md` § 3.)
4. **`Matcher.group()` without a prior successful `find()` / `matches()` throws `System.StringException`.** Always gate. (See `references/gotchas.md` § 4.)
5. **`String.valueOf(null)` returns the four-char string `'null'`, not actual null.** Don't compare its result with `null`. (See `references/gotchas.md` § 5.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Refactored helper class | String/regex helpers with `static final` Patterns and null-safe guards |
| Test class | Coverage for null, empty, validation-pass, validation-fail, extraction-empty, extraction-multi cases |
| Code-review notes | Per call-site: which checklist item motivated the change |

---

## Related Skills

- `apex/dynamic-soql` — String escaping for SOQL injection-safe binds (different escape rules than text rendering)
- `apex/apex-mocking-and-stubs` — when the test class needs to verify regex behavior across edge cases
- `apex/trigger-framework` — when the regex usage lives inside a trigger handler; `static final Pattern` is mandatory there
